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
                patch=(
                    "-ARG USERNAME=developer\n"
                    "+ARG USERNAME=developers"
                ),
            )
        ],
    )

    analyzer = ChangeAnalyzer(db)

    result = analyzer.analyze(
        repository=(
            "asheeshsingh0112/ide"
        ),
        provider="gitlab",
        change_request=change_request,
    )

    assert result.affected_services == [
        "ide-build"
    ]

    assert result.service_mapping_status == "mapped"

    assert result.files_changed == 1
    assert result.lines_added == 1
    assert result.lines_deleted == 1

    assert result.risk_signals == [
        "infrastructure_change"
    ]

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
                patch=(
                    "+New documentation\n"
                    "+More documentation"
                ),
            )
        ],
    )

    analyzer = ChangeAnalyzer(db)

    result = analyzer.analyze(
        repository=(
            "asheeshsingh0112/ide"
        ),
        provider="gitlab",
        change_request=change_request,
    )

    assert result.affected_services == []

    assert result.service_mapping_status == "unmapped"

    assert result.risk_signals == [
        "affected_service_not_identified"
    ]

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
                patch=(
                    "-ARG USERNAME=developer\n"
                    "+ARG USERNAME=developers"
                ),
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