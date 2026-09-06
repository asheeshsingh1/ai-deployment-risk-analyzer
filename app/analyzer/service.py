from sqlalchemy.orm import Session

from app.analyzer.change_signals import ChangeSignalDetector
from app.analyzer.repository import AnalyzerRepository
from app.analyzer.schemas import ChangeAnalysis
from app.scm.schemas import CodeChangeRequest


class ChangeAnalyzer:
    def __init__(self, db: Session):
        self.repository = AnalyzerRepository(db)
        self.signal_detector = ChangeSignalDetector()

    @staticmethod
    def _normalize_path(path: str) -> str:
        return path.strip().lower().strip("/")

    def _find_affected_services(
        self,
        change_request: CodeChangeRequest,
        provider: str,
        owner: str,
        repo_name: str,
    ) -> tuple[list[str], bool]:
        repository = self.repository.get_repository(
            provider=provider,
            owner=owner,
            repo_name=repo_name,
        )

        if repository is None:
            return [], False

        service_paths = self.repository.get_service_paths(
            repository_id=repository.id,
        )

        if not service_paths:
            return [], True

        affected_services: set[str] = set()

        for file in change_request.files:
            file_path = self._normalize_path(
                file.filename
            )

            for service, service_path in service_paths:
                prefix = self._normalize_path(
                    service_path.path_prefix
                )

                if not prefix:
                    continue

                if (
                    file_path == prefix
                    or file_path.startswith(
                        f"{prefix}/"
                    )
                ):
                    affected_services.add(
                        service.name
                    )

        return sorted(affected_services), True

    def analyze(
        self,
        repository: str,
        provider: str,
        change_request: CodeChangeRequest,
    ) -> ChangeAnalysis:
        owner, repo_name = repository.split("/", 1)

        (
            affected_services,
            repository_found,
        ) = self._find_affected_services(
            change_request=change_request,
            provider=provider,
            owner=owner,
            repo_name=repo_name,
        )

        (
            change_types,
            risk_signals,
        ) = self.signal_detector.detect(
            files=change_request.files,
        )

        if not repository_found:
            risk_signals.append(
                "repository_not_registered"
            )

        elif not affected_services:
            risk_signals.append(
                "affected_service_not_identified"
            )

        risk_signals = sorted(set(risk_signals))

        return ChangeAnalysis(
            provider=provider,
            repository=repository,
            change_request_number=change_request.number,
            files_changed=len(change_request.files),
            lines_added=sum(
                file.additions
                for file in change_request.files
            ),
            lines_deleted=sum(
                file.deletions
                for file in change_request.files
            ),
            changed_files=change_request.files,
            affected_services=affected_services,
            change_types=change_types,
            risk_signals=risk_signals,
            service_mapping_status=(
                "mapped"
                if affected_services
                else "unmapped"
            ),
        )