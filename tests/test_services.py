from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from app.db.database import get_db
from app.db.models import Repository, Service, ServicePath
from app.main import app


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
ServicePath.__table__.create(bind=engine)


def override_get_db():
    db = TestingSessionLocal()

    try:
        yield db
    finally:
        db.close()


app.dependency_overrides[get_db] = override_get_db

client = TestClient(app)


def setup_function():
    with TestingSessionLocal() as db:
        db.query(ServicePath).delete()
        db.query(Service).delete()
        db.query(Repository).delete()
        db.commit()


def test_create_repository():
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


def test_create_service():
    repository = Repository(
        name="ide",
        provider="gitlab",
        owner="asheeshsingh0112",
        external_name="ide",
    )

    with TestingSessionLocal() as db:
        db.add(repository)
        db.commit()
        db.refresh(repository)

        repository_id = repository.id

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


def test_create_service_path():
    repository = Repository(
        name="ide",
        provider="gitlab",
        owner="asheeshsingh0112",
        external_name="ide",
    )

    with TestingSessionLocal() as db:
        db.add(repository)
        db.commit()
        db.refresh(repository)

        service = Service(
            name="ide-build",
            repository_id=repository.id,
        )

        db.add(service)
        db.commit()
        db.refresh(service)

        service_id = service.id

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


def test_list_services():
    repository = Repository(
        name="ide",
        provider="gitlab",
        owner="asheeshsingh0112",
        external_name="ide",
    )

    with TestingSessionLocal() as db:
        db.add(repository)
        db.commit()
        db.refresh(repository)

        repository_id = repository.id

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

    response = client.get(
        f"/api/v1/repositories/{repository_id}/services",
    )

    assert response.status_code == 200

    data = response.json()

    assert len(data) == 2
    assert data[0]["name"] == "ide-api"
    assert data[1]["name"] == "ide-build"


def test_list_service_paths():
    repository = Repository(
        name="ide",
        provider="gitlab",
        owner="asheeshsingh0112",
        external_name="ide",
    )

    with TestingSessionLocal() as db:
        db.add(repository)
        db.commit()
        db.refresh(repository)

        service = Service(
            name="ide-build",
            repository_id=repository.id,
        )

        db.add(service)
        db.commit()
        db.refresh(service)

        service_id = service.id

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

    response = client.get(
        f"/api/v1/services/{service_id}/paths",
    )

    assert response.status_code == 200

    data = response.json()

    assert len(data) == 2
    assert data[0]["path_prefix"] == "docker"
    assert data[1]["path_prefix"] == "images"


def test_service_requires_existing_repository():
    response = client.post(
        "/api/v1/repositories/99999/services",
        json={
            "name": "ide-build",
            "repository_id": 99999,
        },
    )

    assert response.status_code == 404


def test_service_path_requires_existing_service():
    response = client.post(
        "/api/v1/services/99999/paths",
        json={
            "path_prefix": "images",
        },
    )

    assert response.status_code == 404


def test_repository_id_mismatch_is_rejected():
    repository = Repository(
        name="ide",
        provider="gitlab",
        owner="asheeshsingh0112",
        external_name="ide",
    )

    with TestingSessionLocal() as db:
        db.add(repository)
        db.commit()
        db.refresh(repository)

        repository_id = repository.id

    response = client.post(
        f"/api/v1/repositories/{repository_id}/services",
        json={
            "name": "ide-build",
            "repository_id": repository_id + 1,
        },
    )

    assert response.status_code == 400
