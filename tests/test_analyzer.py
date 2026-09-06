import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from app.analyzer.service import ChangeAnalyzer
from app.db.models import Repository, Service, ServicePath
from app.scm.schemas import ChangedFile, CodeChangeRequest


@pytest.fixture(autouse=True)
def clean_database():
    yield

    with TestingSessionLocal() as db:
        db.query(ServicePath).delete()
        db.query(Service).delete()
        db.query(Repository).delete()
        db.commit()


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


def create_repository_with_service():
    db = TestingSessionLocal()

    repository = Repository(
        name="ide",
        provider="gitlab",
        owner="asheeshsingh0112",
        external_name="ide",
    )

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

    service_path = ServicePath(
        service_id=service.id,
        path_prefix="images",
    )

    db.add(service_path)
    db.commit()

    return db, repository


def test_changed_file_maps_to_service():
    db, repository = create_repository_with_service()

    change_request = CodeChangeRequest(
        number=1,
        title="Update Docker base image",
        body="Update developer configuration.",
        state="opened",
        base_branch="main",
        head_branch="newbranch",
        head_sha="abc123",
        files=[
            ChangedFile(
                filename="images/Dockerfile.base",
                status="modified",
                additions=1,
                deletions=1,
                changes=2,
                patch=("-ARG USERNAME=developer\n" "+ARG USERNAME=developers"),
            )
        ],
    )

    analyzer = ChangeAnalyzer(db)

    result = analyzer.analyze(
        repository=("asheeshsingh0112/ide"),
        provider="gitlab",
        change_request=change_request,
    )

    assert result.affected_services == ["ide-build"]

    assert result.service_mapping_status == "mapped"

    assert result.files_changed == 1
    assert result.lines_added == 1
    assert result.lines_deleted == 1

    assert result.risk_signals == ["infrastructure_change"]

    db.close()


def test_unmatched_path_is_unmapped():
    db, repository = create_repository_with_service()

    change_request = CodeChangeRequest(
        number=2,
        title="Update documentation",
        body=None,
        state="opened",
        base_branch="main",
        head_branch="docs",
        head_sha="def456",
        files=[
            ChangedFile(
                filename="README.md",
                status="modified",
                additions=2,
                deletions=0,
                changes=2,
                patch=("+New documentation\n" "+More documentation"),
            )
        ],
    )

    analyzer = ChangeAnalyzer(db)

    result = analyzer.analyze(
        repository=("asheeshsingh0112/ide"),
        provider="gitlab",
        change_request=change_request,
    )

    assert result.affected_services == []

    assert result.service_mapping_status == "unmapped"

    assert result.risk_signals == ["affected_service_not_identified"]

    db.close()


def test_unregistered_repository_is_detected():
    db = TestingSessionLocal()

    change_request = CodeChangeRequest(
        number=3,
        title="Change Docker configuration",
        body=None,
        state="opened",
        base_branch="main",
        head_branch="feature",
        head_sha="ghi789",
        files=[
            ChangedFile(
                filename="images/Dockerfile.base",
                status="modified",
                additions=1,
                deletions=1,
                changes=2,
                patch=("-ARG USERNAME=developer\n" "+ARG USERNAME=developers"),
            )
        ],
    )

    analyzer = ChangeAnalyzer(db)

    result = analyzer.analyze(
        repository="unknown/project",
        provider="gitlab",
        change_request=change_request,
    )

    assert result.affected_services == []

    assert result.service_mapping_status == "unmapped"

    assert result.risk_signals == [
        "infrastructure_change",
        "repository_not_registered",
    ]

    db.close()


def test_detects_dependency_change():
    db = TestingSessionLocal()

    change_request = CodeChangeRequest(
        number=4,
        title="Update dependency",
        body=None,
        state="opened",
        base_branch="main",
        head_branch="dependency-update",
        head_sha="jkl012",
        files=[
            ChangedFile(
                filename="package.json",
                status="modified",
                additions=2,
                deletions=1,
                changes=3,
                patch=('-"lodash": "4.17.20"\n' '+"lodash": "4.17.21"\n'),
            )
        ],
    )

    analyzer = ChangeAnalyzer(db)

    result = analyzer.analyze(
        repository="unknown/project",
        provider="github",
        change_request=change_request,
    )

    assert result.change_types == [
        "dependency",
    ]

    assert result.risk_signals == [
        "dependency_change",
        "repository_not_registered",
    ]

    db.close()


def test_detects_security_change():
    db = TestingSessionLocal()

    change_request = CodeChangeRequest(
        number=5,
        title="Update authorization",
        body=None,
        state="opened",
        base_branch="main",
        head_branch="auth-update",
        head_sha="mno345",
        files=[
            ChangedFile(
                filename="api/auth/controller.ts",
                status="modified",
                additions=5,
                deletions=2,
                changes=7,
                patch=("-checkPermission(user)\n" "+checkPermission(user, resource)"),
            )
        ],
    )

    analyzer = ChangeAnalyzer(db)

    result = analyzer.analyze(
        repository="unknown/project",
        provider="github",
        change_request=change_request,
    )

    assert "security" in result.change_types

    assert "authentication_or_authorization_change" in result.risk_signals

    db.close()


def test_detects_potential_breaking_api_change():
    db = TestingSessionLocal()

    change_request = CodeChangeRequest(
        number=6,
        title="Change API response",
        body=None,
        state="opened",
        base_branch="main",
        head_branch="api-update",
        head_sha="pqr678",
        files=[
            ChangedFile(
                filename="api/users/controller.ts",
                status="modified",
                additions=1,
                deletions=1,
                changes=2,
                patch=(
                    "-return res.status(401).json(error)\n"
                    "+return res.status(400).json(error)"
                ),
            )
        ],
    )

    analyzer = ChangeAnalyzer(db)

    result = analyzer.analyze(
        repository="unknown/project",
        provider="github",
        change_request=change_request,
    )

    assert result.change_types == [
        "api",
    ]

    assert "api_change" in result.risk_signals

    assert "potential_breaking_api_change" in result.risk_signals

    db.close()
