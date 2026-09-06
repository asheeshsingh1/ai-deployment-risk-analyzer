from sqlalchemy.orm import Session

from app.analyzer.repository import AnalyzerRepository
from app.analyzer.schemas import ChangeAnalysis
from app.scm.schemas import CodeChangeRequest


class ChangeAnalyzer:
    def __init__(self, db: Session):
        self.repository = AnalyzerRepository(db)

    @staticmethod
    def _normalize_path(path: str) -> str:
        return path.strip().lower().strip("/")

    def _find_affected_services(
        self,
        change_request: CodeChangeRequest,
        owner: str,
        repo_name: str,
    ) -> tuple[list[str], bool]:
        repository = self.repository.get_repository(
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

    def _detect_change_types(
        self,
        change_request: CodeChangeRequest,
    ) -> tuple[list[str], list[str]]:
        change_types: set[str] = set()
        risk_signals: set[str] = set()

        for file in change_request.files:
            filename = file.filename.lower()

            if (
                filename.endswith(".sql")
                or "migration" in filename
                or "/migrations/" in filename
            ):
                change_types.add("database")
                risk_signals.add("database_change")

            if any(
                keyword in filename
                for keyword in (
                    "api",
                    "route",
                    "controller",
                )
            ):
                change_types.add("api")
                risk_signals.add("api_change")

            if any(
                keyword in filename
                for keyword in (
                    "payment",
                    "transaction",
                )
            ):
                change_types.add("business_logic")
                risk_signals.add(
                    "critical_business_logic_change"
                )

            if (
                filename.endswith(".yaml")
                or filename.endswith(".yml")
                or filename.endswith("dockerfile")
            ):
                change_types.add("infrastructure")
                risk_signals.add(
                    "infrastructure_change"
                )

            if (
                filename.endswith("_test.py")
                or filename.startswith("test_")
                or "/tests/" in filename
            ):
                change_types.add("tests")

        return (
            sorted(change_types),
            sorted(risk_signals),
        )

    def analyze(
        self,
        repository: str,
        change_request: CodeChangeRequest,
    ) -> ChangeAnalysis:
        owner, repo_name = repository.split("/", 1)

        (
            affected_services,
            repository_found,
        ) = self._find_affected_services(
            change_request=change_request,
            owner=owner,
            repo_name=repo_name,
        )

        change_types, risk_signals = (
            self._detect_change_types(
                change_request=change_request,
            )
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
            changed_files=[
                file.model_dump()
                for file in change_request.files
            ],
            affected_services=affected_services,
            change_types=change_types,
            risk_signals=risk_signals,
            service_mapping_status=(
                "mapped"
                if affected_services
                else "unmapped"
            ),
        )