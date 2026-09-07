import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from app.db.database import Base, get_db
from app.db.models import Repository, Service, ServicePath
from app.main import app


# =========================================================
# Test database
# =========================================================

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


def create_repository():
    db = TestingSessionLocal()

    try:
        repository = Repository(
            name="ide",
            provider="gitlab",
            owner="asheeshsingh0112",
            external_name="ide",
        )

        db.add(repository)
        db.commit()
        db.refresh(repository)

        return repository.id

    finally:
        db.close()


def create_service(repository_id: int):
    db = TestingSessionLocal()

    try:
        service = Service(
            name="ide-build",
            repository_id=repository_id,
        )

        db.add(service)
        db.commit()
        db.refresh(service)

        return service.id

    finally:
        db.close()


# =========================================================
# Repository
# =========================================================


def test_create_repository(client):
    response = client.post(
        "/api/v1/repositories",
        json={
            "name": "ide",
            "provider": "gitlab",
            "owner": "asheeshsingh0112",
            "external_name": "ide",
        },
    )

    assert response.status_code == 201

    data = response.json()

    assert data["name"] == "ide"
    assert data["provider"] == "gitlab"
    assert data["owner"] == "asheeshsingh0112"
    assert data["external_name"] == "ide"


# =========================================================
# Service
# =========================================================


def test_create_service(client):
    repository_id = create_repository()

    response = client.post(
        f"/api/v1/repositories/{repository_id}/services",
        json={
            "name": "ide-build",
            "repository_id": repository_id,
        },
    )

    assert response.status_code == 201

    data = response.json()

    assert data["name"] == "ide-build"
    assert data["repository_id"] == repository_id


def test_create_service_path(client):
    repository_id = create_repository()
    service_id = create_service(repository_id)

    response = client.post(
        f"/api/v1/services/{service_id}/paths",
        json={
            "path_prefix": "/images/",
        },
    )

    assert response.status_code == 201

    data = response.json()

    assert data["service_id"] == service_id
    assert data["path_prefix"] == "images"


# =========================================================
# Service listing
# =========================================================


def test_list_services(client):
    repository_id = create_repository()

    db = TestingSessionLocal()

    try:
        db.add(
            Service(
                name="ide-build",
                repository_id=repository_id,
            )
        )

        db.add(
            Service(
                name="ide-api",
                repository_id=repository_id,
            )
        )

        db.commit()

    finally:
        db.close()

    response = client.get(
        f"/api/v1/repositories/{repository_id}/services",
    )

    assert response.status_code == 200

    data = response.json()

    assert len(data) == 2
    assert data[0]["name"] == "ide-api"
    assert data[1]["name"] == "ide-build"


def test_list_service_paths(client):
    repository_id = create_repository()
    service_id = create_service(repository_id)

    db = TestingSessionLocal()

    try:
        db.add(
            ServicePath(
                service_id=service_id,
                path_prefix="images",
            )
        )

        db.add(
            ServicePath(
                service_id=service_id,
                path_prefix="docker",
            )
        )

        db.commit()

    finally:
        db.close()

    response = client.get(
        f"/api/v1/services/{service_id}/paths",
    )

    assert response.status_code == 200

    data = response.json()

    assert len(data) == 2
    assert data[0]["path_prefix"] == "docker"
    assert data[1]["path_prefix"] == "images"


# =========================================================
# Validation / not found
# =========================================================


def test_service_requires_existing_repository(client):
    response = client.post(
        "/api/v1/repositories/99999/services",
        json={
            "name": "ide-build",
            "repository_id": 99999,
        },
    )

    assert response.status_code == 404


def test_service_path_requires_existing_service(client):
    response = client.post(
        "/api/v1/services/99999/paths",
        json={
            "path_prefix": "images",
        },
    )

    assert response.status_code == 404


def test_repository_id_mismatch_is_rejected(client):
    repository_id = create_repository()

    response = client.post(
        f"/api/v1/repositories/{repository_id}/services",
        json={
            "name": "ide-build",
            "repository_id": repository_id + 1,
        },
    )

    assert response.status_code == 400
