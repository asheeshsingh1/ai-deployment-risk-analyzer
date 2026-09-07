from dataclasses import dataclass

from sqlalchemy.orm import Session

from app.analyzer.repository import AnalyzerRepository
from app.scm.schemas import CodeChangeRequest


@dataclass(frozen=True)
class RepositoryRegistration:
    repository_id: int
    created: bool


@dataclass(frozen=True)
class ServiceRegistration:
    service_id: int
    service_name: str
    created: bool


class AnalyzerRegistry:
    """
    Ensures repositories and services exist before analysis.

    Explicit ServicePath mappings remain the source of truth when
    they exist. Automatic service registration is only a fallback
    for previously unknown repositories.
    """

    def __init__(self, db: Session):
        self.repository = AnalyzerRepository(db)

    def ensure_repository(
        self,
        provider: str,
        owner: str,
        repo_name: str,
    ) -> RepositoryRegistration:
        repository, created = self.repository.get_or_create_repository(
            provider=provider,
            owner=owner,
            repo_name=repo_name,
        )

        return RepositoryRegistration(
            repository_id=repository.id,
            created=created,
        )

    @staticmethod
    def _normalize_path(path: str) -> str:
        return path.strip().lower().strip("/")

    @classmethod
    def _infer_service_name(
        cls,
        change_request: CodeChangeRequest,
    ) -> str:
        """
        Infer a stable service name from changed files.

        The first meaningful directory is used as the service
        boundary. Root-level files fall back to repository-service.
        """

        for file in change_request.files:
            normalized_path = cls._normalize_path(
                file.filename,
            )

            if not normalized_path:
                continue

            parts = [part for part in normalized_path.split("/") if part]

            if len(parts) >= 2:
                directory = parts[0]
                return f"{directory}-service"

        return "repository-service"

    def ensure_service(
        self,
        repository_id: int,
        change_request: CodeChangeRequest,
    ) -> ServiceRegistration:
        service_name = self._infer_service_name(
            change_request,
        )

        service, created = self.repository.get_or_create_service(
            repository_id=repository_id,
            service_name=service_name,
        )

        return ServiceRegistration(
            service_id=service.id,
            service_name=service.name,
            created=created,
        )
