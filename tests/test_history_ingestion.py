from datetime import datetime, timezone

import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from app.db.models import (
    Deployment,
    DeploymentStatus,
    Incident,
    IncidentSeverity,
    Repository,
    Service,
)
from app.history.ingestion import HistoryIngestionService
from app.history.repository import HistoryRepository
from app.history.schemas import (
    DeploymentIngestionRequest,
    IncidentIngestionRequest,
)
from fastapi.testclient import TestClient

from app.db.database import get_db
from app.main import app

client = TestClient(app)


engine = create_engine(
    "sqlite:///:memory:",
    connect_args={"check_same_thread": False},
    poolclass=StaticPool,
)

TestingSessionLocal = sessionmaker(
    bind=engine,
    autoflush=False,
    autocommit=False,
)

Repository.__table__.create(bind=engine)
Service.__table__.create(bind=engine)
Deployment.__table__.create(bind=engine)
Incident.__table__.create(bind=engine)


@pytest.fixture(autouse=True)
def clean_database():
    yield

    with TestingSessionLocal() as db:
        db.query(Incident).delete()
        db.query(Deployment).delete()
        db.query(Service).delete()
        db.query(Repository).delete()
        db.commit()


@pytest.fixture
def service():
    with TestingSessionLocal() as db:
        repository = Repository(
            name="tasker",
            provider="github",
            owner="owner",
            external_name="tasker",
        )

        db.add(repository)
        db.flush()

        service = Service(
            repository_id=repository.id,
            name="tasker-service",
        )

        db.add(service)
        db.commit()
        db.refresh(repository)
        db.refresh(service)

        return repository.id, service.id


def test_ingest_deployment(service):
    repository_id, service_id = service

    with TestingSessionLocal() as db:
        ingestion = HistoryIngestionService(
            HistoryRepository(db),
        )

        result = ingestion.ingest_deployment(
            DeploymentIngestionRequest(
                repository_id=repository_id,
                service_id=service_id,
                commit_sha="abc123",
                status=DeploymentStatus.SUCCESS,
                deployed_at=datetime.now(timezone.utc),
            )
        )

        assert result.created is True
        assert result.repository_id == repository_id
        assert result.service_id == service_id
        assert result.commit_sha == "abc123"
        assert result.status == DeploymentStatus.SUCCESS


def test_duplicate_deployment_is_not_created(service):
    repository_id, service_id = service

    request = DeploymentIngestionRequest(
        repository_id=repository_id,
        service_id=service_id,
        commit_sha="abc123",
        status=DeploymentStatus.SUCCESS,
        deployed_at=datetime.now(timezone.utc),
    )

    with TestingSessionLocal() as db:
        ingestion = HistoryIngestionService(
            HistoryRepository(db),
        )

        first = ingestion.ingest_deployment(request)
        second = ingestion.ingest_deployment(request)

        assert first.created is True
        assert second.created is False
        assert first.id == second.id

        assert db.query(Deployment).count() == 1


def test_ingest_deployment_rejects_wrong_repository(service):
    repository_id, service_id = service

    with TestingSessionLocal() as db:
        other_repository = Repository(
            name="other",
            provider="github",
            owner="owner",
            external_name="other",
        )

        db.add(other_repository)
        db.commit()
        db.refresh(other_repository)

        ingestion = HistoryIngestionService(
            HistoryRepository(db),
        )

        with pytest.raises(
            ValueError,
            match="does not belong",
        ):
            ingestion.ingest_deployment(
                DeploymentIngestionRequest(
                    repository_id=other_repository.id,
                    service_id=service_id,
                    commit_sha="abc123",
                    status=DeploymentStatus.SUCCESS,
                    deployed_at=datetime.now(timezone.utc),
                )
            )


def test_ingest_deployment_rejects_unknown_service():
    with TestingSessionLocal() as db:
        ingestion = HistoryIngestionService(
            HistoryRepository(db),
        )

        with pytest.raises(
            ValueError,
            match="does not exist",
        ):
            ingestion.ingest_deployment(
                DeploymentIngestionRequest(
                    repository_id=1,
                    service_id=999,
                    commit_sha="abc123",
                    status=DeploymentStatus.SUCCESS,
                    deployed_at=datetime.now(timezone.utc),
                )
            )


def test_ingest_incident(service):
    _, service_id = service

    with TestingSessionLocal() as db:
        ingestion = HistoryIngestionService(
            HistoryRepository(db),
        )

        started_at = datetime.now(timezone.utc)

        result = ingestion.ingest_incident(
            IncidentIngestionRequest(
                service_id=service_id,
                title="API outage",
                description="The API returned elevated 5xx responses.",
                severity=IncidentSeverity.HIGH,
                started_at=started_at,
            )
        )

        assert result.created is True
        assert result.service_id == service_id
        assert result.title == "API outage"
        assert result.severity == IncidentSeverity.HIGH


def test_duplicate_incident_is_not_created(service):
    _, service_id = service

    started_at = datetime.now(timezone.utc)

    request = IncidentIngestionRequest(
        service_id=service_id,
        title="API outage",
        description="The API returned elevated 5xx responses.",
        severity=IncidentSeverity.HIGH,
        started_at=started_at,
    )

    with TestingSessionLocal() as db:
        ingestion = HistoryIngestionService(
            HistoryRepository(db),
        )

        first = ingestion.ingest_incident(request)
        second = ingestion.ingest_incident(request)

        assert first.created is True
        assert second.created is False
        assert first.id == second.id

        assert db.query(Incident).count() == 1


@pytest.fixture
def api_client():
    previous_overrides = app.dependency_overrides.copy()

    def override_get_db():
        db = TestingSessionLocal()
        try:
            yield db
        finally:
            db.close()

    app.dependency_overrides[get_db] = override_get_db

    try:
        yield client
    finally:
        app.dependency_overrides.clear()
        app.dependency_overrides.update(previous_overrides)


def test_deployment_ingestion_api(api_client, service):
    repository_id, service_id = service

    response = api_client.post(
        "/api/v1/history/deployments",
        json={
            "repository_id": repository_id,
            "service_id": service_id,
            "commit_sha": "api-commit-123",
            "status": "success",
            "deployed_at": "2026-09-06T12:00:00Z",
        },
    )

    assert response.status_code == 201

    data = response.json()

    assert data["repository_id"] == repository_id
    assert data["service_id"] == service_id
    assert data["commit_sha"] == "api-commit-123"
    assert data["status"] == "success"
    assert data["created"] is True


def test_incident_ingestion_api(api_client, service):
    _, service_id = service

    response = api_client.post(
        "/api/v1/history/incidents",
        json={
            "service_id": service_id,
            "title": "Database latency",
            "description": "Database latency exceeded the threshold.",
            "severity": "medium",
            "started_at": "2026-09-06T12:00:00Z",
        },
    )

    assert response.status_code == 201

    data = response.json()

    assert data["service_id"] == service_id
    assert data["title"] == "Database latency"
    assert data["severity"] == "medium"
    assert data["created"] is True
