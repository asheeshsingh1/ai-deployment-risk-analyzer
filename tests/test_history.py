from datetime import datetime, timedelta, timezone

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
from app.history.service import (
    HistoricalIntelligenceService,
)
from app.risk.repository import RiskRepository


engine = create_engine(
    "sqlite:///:memory:",
    connect_args={
        "check_same_thread": False,
    },
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


def create_service():
    db = TestingSessionLocal()

    repository = Repository(
        name="history-test",
        provider="github",
        owner="test-owner",
        external_name="history-test",
    )

    db.add(repository)
    db.commit()
    db.refresh(repository)

    service = Service(
        name="history-service",
        repository_id=repository.id,
    )

    db.add(service)
    db.commit()
    db.refresh(service)

    return db, service


def test_historical_deployment_statistics():
    db, service = create_service()

    now = datetime.now(timezone.utc)

    statuses = [
        DeploymentStatus.SUCCESS,
        DeploymentStatus.SUCCESS,
        DeploymentStatus.FAILED,
        DeploymentStatus.ROLLED_BACK,
    ]

    for index, status in enumerate(statuses):
        db.add(
            Deployment(
                repository_id=service.repository_id,
                service_id=service.id,
                commit_sha=f"sha-{index}",
                status=status,
                deployed_at=now - timedelta(days=index),
            )
        )

    db.commit()

    repository = RiskRepository(db)

    historical_service = HistoricalIntelligenceService(
        repository=repository,
    )

    result = historical_service.analyze(
        service_id=service.id,
        service_name=service.name,
    )

    assert result.deployments.total_deployments == 4

    assert result.deployments.successful_deployments == 2

    assert result.deployments.failed_deployments == 1

    assert result.deployments.rolled_back_deployments == 1

    assert result.deployments.failure_rate == 0.5

    assert result.deployments.rollback_rate == 0.25

    assert result.deployments.recent_deployments == 4

    db.close()


def test_historical_incident_statistics():
    db, service = create_service()

    now = datetime.now(timezone.utc)

    severities = [
        IncidentSeverity.LOW,
        IncidentSeverity.MEDIUM,
        IncidentSeverity.HIGH,
        IncidentSeverity.CRITICAL,
    ]

    for index, severity in enumerate(severities):
        db.add(
            Incident(
                service_id=service.id,
                title=f"Incident {index}",
                description="Historical incident",
                severity=severity,
                started_at=now - timedelta(days=index),
                resolved_at=now - timedelta(days=index),
            )
        )

    db.commit()

    repository = RiskRepository(db)

    historical_service = HistoricalIntelligenceService(
        repository=repository,
    )

    result = historical_service.analyze(
        service_id=service.id,
        service_name=service.name,
    )

    assert result.incidents.total_incidents == 4

    assert result.incidents.low_severity == 1
    assert result.incidents.medium_severity == 1
    assert result.incidents.high_severity == 1
    assert result.incidents.critical_severity == 1

    assert result.incidents.recent_incidents == 4

    db.close()


def test_no_historical_data():
    db, service = create_service()

    repository = RiskRepository(db)

    historical_service = HistoricalIntelligenceService(
        repository=repository,
    )

    result = historical_service.analyze(
        service_id=service.id,
        service_name=service.name,
    )

    assert result.deployments.total_deployments == 0
    assert result.deployments.failure_rate == 0.0

    assert result.incidents.total_incidents == 0

    assert any("No deployment history" in evidence for evidence in result.evidence)

    assert any("No incidents" in evidence for evidence in result.evidence)

    db.close()
