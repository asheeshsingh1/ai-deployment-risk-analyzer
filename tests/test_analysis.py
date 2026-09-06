from unittest.mock import Mock

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from app.db.database import get_db
from app.db.models import Repository, Service, ServicePath
from app.main import app


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
ServicePath.__table__.create(bind=engine)


@pytest.fixture(autouse=True)
def clean_database():
    yield

    with TestingSessionLocal() as db:
        db.query(ServicePath).delete()
        db.query(Service).delete()
        db.query(Repository).delete()
        db.commit()


@pytest.fixture
def client():
    previous_overrides = app.dependency_overrides.copy()

    def override_get_db():
        db = TestingSessionLocal()
        try:
            yield db
        finally:
            db.close()

    app.dependency_overrides[get_db] = override_get_db

    try:
        yield TestClient(app)
    finally:
        app.dependency_overrides.clear()
        app.dependency_overrides.update(previous_overrides)


def create_service():
    with TestingSessionLocal() as db:
        repository = Repository(
            name="tasker",
            provider="github",
            owner="asheeshsingh1",
            external_name="tasker",
        )

        db.add(repository)
        db.flush()

        service = Service(
            repository_id=repository.id,
            name="tasker-service",
        )

        db.add(service)
        db.flush()

        db.add(
            ServicePath(
                service_id=service.id,
                path_prefix="api",
            )
        )

        db.commit()


def mock_change_request():
    change_request = Mock()

    change_request.number = 1
    change_request.title = "status code changed"
    change_request.body = "Test change"
    change_request.state = "open"
    change_request.base_branch = "main"
    change_request.head_branch = "feature/test"
    change_request.head_sha = "abc123"

    change_request.files = []

    return change_request


def test_local_analysis_endpoint(client, monkeypatch):
    create_service()

    provider = Mock()
    provider.get_change_request.return_value = mock_change_request()

    monkeypatch.setattr(
        "app.api.analysis.get_scm_provider",
        lambda provider_name: provider,
    )

    response = client.post(
        "/api/v1/analysis",
        json={
            "provider": "github",
            "owner": "asheeshsingh1",
            "repository": "tasker",
            "change_number": 1,
        },
    )

    assert response.status_code == 200

    data = response.json()

    assert data["repository"] == "asheeshsingh1/tasker"
    assert data["change_request_number"] == 1
    assert data["affected_services"] == []
    assert data["overall_score"] == 0


def test_local_analysis_rejects_invalid_change_number(client):
    response = client.post(
        "/api/v1/analysis",
        json={
            "provider": "github",
            "owner": "asheeshsingh1",
            "repository": "tasker",
            "change_number": 0,
        },
    )

    assert response.status_code == 422


def test_local_analysis_rejects_missing_provider(client):
    response = client.post(
        "/api/v1/analysis",
        json={
            "owner": "asheeshsingh1",
            "repository": "tasker",
            "change_number": 1,
        },
    )

    assert response.status_code == 422


def test_local_analysis_handles_scm_not_found(client, monkeypatch):
    from app.scm.exceptions import SCMNotFoundError

    provider = Mock()

    provider.get_change_request.side_effect = SCMNotFoundError(
        "GitHub resource was not found.",
        provider="github",
        status_code=404,
    )

    monkeypatch.setattr(
        "app.api.analysis.get_scm_provider",
        lambda provider_name: provider,
    )

    response = client.post(
        "/api/v1/analysis",
        json={
            "provider": "github",
            "owner": "asheeshsingh1",
            "repository": "tasker",
            "change_number": 999,
        },
    )

    assert response.status_code == 404

    data = response.json()

    assert data["detail"]["error"] == "scm_resource_not_found"
