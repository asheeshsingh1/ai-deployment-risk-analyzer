from sqlalchemy import select
from sqlalchemy.orm import Session

from app.db.models import Repository, Service, ServicePath


class AnalyzerRepository:
    def __init__(self, db: Session):
        self.db = db

    def get_repository(
        self,
        provider: str,
        owner: str,
        repo_name: str,
    ) -> Repository | None:
        statement = select(Repository).where(
            Repository.provider == provider,
            Repository.owner == owner,
            Repository.external_name == repo_name,
        )

        return self.db.scalar(statement)

    def get_services(
        self,
        repository_id: int,
    ) -> list[Service]:
        statement = (
            select(Service)
            .where(Service.repository_id == repository_id)
            .order_by(Service.name)
        )

        return list(
            self.db.scalars(statement).all()
        )

    def get_service_paths(
        self,
        repository_id: int,
    ) -> list[tuple[Service, ServicePath]]:
        statement = (
            select(Service, ServicePath)
            .join(
                ServicePath,
                ServicePath.service_id == Service.id,
            )
            .where(
                Service.repository_id == repository_id,
            )
            .order_by(
                ServicePath.path_prefix,
            )
        )

        return list(
            self.db.execute(statement).all()
        )