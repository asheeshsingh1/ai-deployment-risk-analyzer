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

    def get_or_create_repository(
        self,
        provider: str,
        owner: str,
        repo_name: str,
    ) -> tuple[Repository, bool]:
        repository = self.get_repository(
            provider=provider,
            owner=owner,
            repo_name=repo_name,
        )

        if repository is not None:
            return repository, False

        repository = Repository(
            name=repo_name,
            provider=provider,
            owner=owner,
            external_name=repo_name,
        )

        self.db.add(repository)

        try:
            self.db.flush()
        except Exception:
            self.db.rollback()

            repository = self.get_repository(
                provider=provider,
                owner=owner,
                repo_name=repo_name,
            )

            if repository is None:
                raise

            return repository, False

        return repository, True

    def get_services(
        self,
        repository_id: int,
    ) -> list[Service]:
        statement = (
            select(Service)
            .where(Service.repository_id == repository_id)
            .order_by(Service.name)
        )

        return list(self.db.scalars(statement).all())

    def get_service(
        self,
        repository_id: int,
        service_name: str,
    ) -> Service | None:
        statement = select(Service).where(
            Service.repository_id == repository_id,
            Service.name == service_name,
        )

        return self.db.scalar(statement)

    def get_or_create_service(
        self,
        repository_id: int,
        service_name: str,
    ) -> tuple[Service, bool]:
        service = self.get_service(
            repository_id=repository_id,
            service_name=service_name,
        )

        if service is not None:
            return service, False

        service = Service(
            repository_id=repository_id,
            name=service_name,
        )

        self.db.add(service)

        try:
            self.db.flush()
        except Exception:
            self.db.rollback()

            service = self.get_service(
                repository_id=repository_id,
                service_name=service_name,
            )

            if service is None:
                raise

            return service, False

        return service, True

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

        return list(self.db.execute(statement).all())
