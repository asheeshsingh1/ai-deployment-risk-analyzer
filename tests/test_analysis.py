from unittest.mock import Mock

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from app.db.database import Base, get_db
from app.db.models import Repository, Service, ServicePath
from app.main import app
from app.risk.schemas import ChangeRequestRiskAssessment
from app.scm.schemas import ChangedFile, CodeChangeRequest


# =========================================================
# Test database
# =========================================================

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

Base.metadata.create_all(bind=engine)


# =========================================================
# Fixtures
# =========================================================


@pytest.fixture(autouse=True)
def clean_database():
    db = TestingSessionLocal()

    try:
        yield
    finally:
        db.rollback()

        db.query(ServicePath).delete()
        db.query(Service).delete()
        db.query(Repository).delete()

        db.commit()
        db.close()


@pytest.fixture
def client():
    def override_get_db():
        db = TestingSessionLocal()

        try:
            yield db
        finally:
            db.close()

    app.dependency_overrides[get_db] = override_get_db

    with TestClient(app) as test_client:
        yield test_client

    app.dependency_overrides.clear()


# =========================================================
# Helpers
# =========================================================


def create_repository(
    owner: str = "asheeshsingh1",
    repository: str = "tasker",
    provider: str = "github",
):
    db = TestingSessionLocal()

    try:
        repo = Repository(
            name=repository,
            provider=provider,
            owner=owner,
            external_name=repository,
        )

        db.add(repo)
        db.flush()

        service = Service(
            repository_id=repo.id,
            name="tasker-service",
        )

        db.add(service)
        db.flush()

        service_path = ServicePath(
            service_id=service.id,
            path_prefix="src",
        )

        db.add(service_path)
        db.commit()

        return repo.id

    finally:
        db.close()


def mock_change_request(number: int = 1):
    return CodeChangeRequest(
        number=number,
        title="Test change",
        body="Test change body",
        state="open",
        base_branch="main",
        head_branch="feature",
        head_sha="abc123",
        files=[
            ChangedFile(
                filename="src/main.py",
                status="modified",
                additions=10,
                deletions=5,
                changes=15,
                patch=("@@ -1,5 +1,10 @@\n" "-old code\n" "+new code\n"),
            )
        ],
    )


def mock_risk_assessment(
    repository: str = "asheeshsingh1/tasker",
    change_request_number: int = 1,
):
    return ChangeRequestRiskAssessment(
        repository=repository,
        change_request_number=change_request_number,
        change_request_title="Test change",
        affected_services=["tasker-service"],
        change_types=["application"],
        risk_signals=[],
        files_changed=1,
        lines_added=10,
        lines_deleted=5,
        changed_files=[
            ChangedFile(
                filename="src/main.py",
                status="modified",
                additions=10,
                deletions=5,
                changes=15,
                patch=("@@ -1,5 +1,10 @@\n" "-old code\n" "+new code\n"),
            )
        ],
        service_assessments=[],
        overall_score=10,
        overall_level="low",
        recommendation="Proceed with normal deployment safeguards.",
        ai_explanation="Test AI explanation.",
        ai_recommendation="Test AI recommendation.",
    )


# =========================================================
# Successful analysis
# =========================================================


def test_local_analysis_endpoint(
    client,
    monkeypatch,
):
    create_repository()

    provider = Mock()

    provider.get_change_request.return_value = mock_change_request()

    monkeypatch.setattr(
        "app.api.analysis.get_scm_provider",
        lambda provider_name: provider,
    )

    monkeypatch.setattr(
        "app.api.analysis.ChangeRequestRiskService.assess",
        Mock(return_value=mock_risk_assessment()),
    )

    response = client.post(
        "/api/v1/analysis",
        json={
            "change_request_url": ("https://github.com/" "asheeshsingh1/tasker/pull/1"),
        },
    )

    assert response.status_code == 200

    body = response.json()

    assert body["repository"] == ("asheeshsingh1/tasker")

    assert body["change_request_number"] == 1

    assert body["change_request_title"] == ("Test change")

    assert body["files_changed"] == 1
    assert body["lines_added"] == 10
    assert body["lines_deleted"] == 5

    provider.get_change_request.assert_called_once_with(
        owner="asheeshsingh1",
        repository="tasker",
        change_number=1,
    )


# =========================================================
# Invalid URL
# =========================================================


def test_local_analysis_rejects_invalid_change_request_url(
    client,
):
    response = client.post(
        "/api/v1/analysis",
        json={
            "change_request_url": ("https://github.com/" "example/project/issues/1"),
        },
    )

    assert response.status_code == 400

    body = response.json()

    assert body["detail"]["error"] == ("invalid_change_request_url")


def test_local_analysis_rejects_unsupported_provider_url(
    client,
):
    response = client.post(
        "/api/v1/analysis",
        json={
            "change_request_url": (
                "https://bitbucket.org/" "example/project/pull-requests/1"
            ),
        },
    )

    assert response.status_code == 400

    body = response.json()

    assert body["detail"]["error"] == ("invalid_change_request_url")


# =========================================================
# SCM not found
# =========================================================


def test_local_analysis_handles_scm_not_found(
    client,
    monkeypatch,
):
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
            "change_request_url": (
                "https://github.com/" "asheeshsingh1/tasker/pull/999"
            ),
        },
    )

    assert response.status_code == 404

    body = response.json()

    assert body["detail"]["error"] == ("scm_resource_not_found")

    assert body["detail"]["provider"] == "github"

    provider.get_change_request.assert_called_once_with(
        owner="asheeshsingh1",
        repository="tasker",
        change_number=999,
    )


# =========================================================
# SCM authentication error
# =========================================================


def test_local_analysis_handles_scm_authentication_error(
    client,
    monkeypatch,
):
    from app.scm.exceptions import SCMAuthenticationError

    provider = Mock()

    provider.get_change_request.side_effect = SCMAuthenticationError(
        "GitHub authentication failed.",
        provider="github",
        status_code=401,
    )

    monkeypatch.setattr(
        "app.api.analysis.get_scm_provider",
        lambda provider_name: provider,
    )

    response = client.post(
        "/api/v1/analysis",
        json={
            "change_request_url": ("https://github.com/" "asheeshsingh1/tasker/pull/1"),
        },
    )

    assert response.status_code == 502

    body = response.json()

    assert body["detail"]["error"] == ("scm_authentication_failed")

    assert body["detail"]["provider"] == "github"


# =========================================================
# SCM rate limit
# =========================================================


def test_local_analysis_handles_scm_rate_limit(
    client,
    monkeypatch,
):
    from app.scm.exceptions import SCMRateLimitError

    provider = Mock()

    provider.get_change_request.side_effect = SCMRateLimitError(
        "GitHub rate limit exceeded.",
        provider="github",
        status_code=429,
    )

    monkeypatch.setattr(
        "app.api.analysis.get_scm_provider",
        lambda provider_name: provider,
    )

    response = client.post(
        "/api/v1/analysis",
        json={
            "change_request_url": ("https://github.com/" "asheeshsingh1/tasker/pull/1"),
        },
    )

    assert response.status_code == 429

    body = response.json()

    assert body["detail"]["error"] == ("scm_rate_limit_exceeded")

    assert body["detail"]["provider"] == "github"


# =========================================================
# Generic SCM error
# =========================================================


def test_local_analysis_handles_generic_scm_error(
    client,
    monkeypatch,
):
    from app.scm.exceptions import SCMProviderError

    provider = Mock()

    provider.get_change_request.side_effect = SCMProviderError(
        "GitHub provider failed.",
        provider="github",
        status_code=500,
    )

    monkeypatch.setattr(
        "app.api.analysis.get_scm_provider",
        lambda provider_name: provider,
    )

    response = client.post(
        "/api/v1/analysis",
        json={
            "change_request_url": ("https://github.com/" "asheeshsingh1/tasker/pull/1"),
        },
    )

    assert response.status_code == 502

    body = response.json()

    assert body["detail"]["error"] == ("scm_provider_error")

    assert body["detail"]["provider"] == "github"


# =========================================================
# Invalid provider handling
# =========================================================


def test_local_analysis_handles_invalid_provider(
    client,
    monkeypatch,
):
    monkeypatch.setattr(
        "app.api.analysis.get_scm_provider",
        Mock(side_effect=ValueError("Unsupported SCM provider: bitbucket")),
    )

    response = client.post(
        "/api/v1/analysis",
        json={
            "change_request_url": ("https://github.com/" "asheeshsingh1/tasker/pull/1"),
        },
    )

    assert response.status_code == 400

    body = response.json()

    assert body["detail"] == ("Unsupported SCM provider: bitbucket")


# =========================================================
# GitLab URL
# =========================================================


def test_local_analysis_accepts_gitlab_merge_request(
    client,
    monkeypatch,
):
    provider = Mock()

    provider.get_change_request.return_value = mock_change_request()

    monkeypatch.setattr(
        "app.api.analysis.get_scm_provider",
        lambda provider_name: provider,
    )

    monkeypatch.setattr(
        "app.api.analysis.ChangeRequestRiskService.assess",
        Mock(
            return_value=mock_risk_assessment(
                repository="asheeshsingh0112/ide",
                change_request_number=1,
            )
        ),
    )

    response = client.post(
        "/api/v1/analysis",
        json={
            "change_request_url": (
                "https://gitlab.com/" "asheeshsingh0112/" "ide/" "-/merge_requests/1"
            ),
        },
    )

    assert response.status_code == 200

    body = response.json()

    assert body["repository"] == ("asheeshsingh0112/ide")

    assert body["change_request_number"] == 1

    provider.get_change_request.assert_called_once_with(
        owner="asheeshsingh0112",
        repository="ide",
        change_number=1,
    )
