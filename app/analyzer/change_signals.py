from app.scm.schemas import ChangedFile


class ChangeSignalDetector:
    """
    Deterministically detects risk-relevant characteristics
    from changed files and their patches.

    This component does not calculate a risk score.
    It only produces evidence/signals that the risk engine
    can consume later.
    """

    API_KEYWORDS = (
        "api",
        "route",
        "routes",
        "controller",
        "handler",
        "endpoint",
    )

    DATABASE_KEYWORDS = (
        "migration",
        "migrations",
        "schema",
        "models",
        "repository",
        "repositories",
    )

    AUTH_KEYWORDS = (
        "auth",
        "authentication",
        "authorization",
        "permission",
        "permissions",
        "rbac",
        "jwt",
        "oauth",
        "session",
    )

    DEPENDENCY_FILES = (
        "package.json",
        "package-lock.json",
        "yarn.lock",
        "pnpm-lock.yaml",
        "requirements.txt",
        "requirements-dev.txt",
        "poetry.lock",
        "pyproject.toml",
        "pipfile",
        "pipfile.lock",
        "go.mod",
        "go.sum",
        "cargo.toml",
        "cargo.lock",
    )

    CONFIG_EXTENSIONS = (
        ".env",
        ".ini",
        ".conf",
        ".cfg",
        ".properties",
        ".toml",
        ".json",
        ".yaml",
        ".yml",
    )

    INFRASTRUCTURE_EXTENSIONS = (
        ".dockerfile",
        ".yaml",
        ".yml",
        ".tf",
        ".tfvars",
    )

    @staticmethod
    def _filename(file: ChangedFile) -> str:
        return file.filename.strip().lower()

    @staticmethod
    def _patch(file: ChangedFile) -> str:
        return file.patch or ""

    @classmethod
    def _contains_keyword(
        cls,
        filename: str,
        keywords: tuple[str, ...],
    ) -> bool:
        return any(
            keyword in filename
            for keyword in keywords
        )

    @classmethod
    def _is_dockerfile(
        cls,
        filename: str,
    ) -> bool:
        basename = filename.rsplit("/", 1)[-1]

        return (
            basename == "dockerfile"
            or basename.startswith("dockerfile.")
        )

    @classmethod
    def _is_dependency_file(
        cls,
        filename: str,
    ) -> bool:
        basename = filename.rsplit("/", 1)[-1]

        return basename in cls.DEPENDENCY_FILES

    @classmethod
    def _is_configuration_file(
        cls,
        filename: str,
    ) -> bool:
        basename = filename.rsplit("/", 1)[-1]

        return (
            basename.startswith(".env")
            or basename.endswith(
                cls.CONFIG_EXTENSIONS
            )
        )

    @classmethod
    def _is_infrastructure_file(
        cls,
        filename: str,
    ) -> bool:
        return (
            cls._is_dockerfile(filename)
            or filename.endswith(
                cls.INFRASTRUCTURE_EXTENSIONS
            )
            or "/k8s/" in f"/{filename}/"
            or "/kubernetes/" in f"/{filename}/"
            or "/helm/" in f"/{filename}/"
            or "/terraform/" in f"/{filename}/"
        )

    @classmethod
    def _has_auth_change(
        cls,
        filename: str,
        patch: str,
    ) -> bool:
        return cls._contains_keyword(
            filename,
            cls.AUTH_KEYWORDS,
        ) or any(
            keyword in patch.lower()
            for keyword in cls.AUTH_KEYWORDS
        )

    @staticmethod
    def _has_breaking_api_change(
        patch: str,
    ) -> bool:
        patch_lower = patch.lower()

        breaking_patterns = (
            "status(",
            "status_code",
            "status code",
            "delete(",
            "removed",
            "breaking",
            "required",
            "response_model",
            "request_model",
        )

        return any(
            pattern in patch_lower
            for pattern in breaking_patterns
        )

    @staticmethod
    def _is_large_change(
        file: ChangedFile,
    ) -> bool:
        return file.changes >= 100

    @classmethod
    def detect(
        cls,
        files: list[ChangedFile],
    ) -> tuple[list[str], list[str]]:
        change_types: set[str] = set()
        risk_signals: set[str] = set()

        total_changes = sum(
            file.changes
            for file in files
        )

        for file in files:
            filename = cls._filename(file)
            patch = cls._patch(file)

            if cls._is_infrastructure_file(filename):
                change_types.add("infrastructure")
                risk_signals.add(
                    "infrastructure_change"
                )

            if (
                filename.endswith(".sql")
                or cls._contains_keyword(
                    filename,
                    cls.DATABASE_KEYWORDS,
                )
            ):
                change_types.add("database")
                risk_signals.add(
                    "database_change"
                )

            if cls._contains_keyword(
                filename,
                cls.API_KEYWORDS,
            ):
                change_types.add("api")
                risk_signals.add(
                    "api_change"
                )

                if cls._has_breaking_api_change(patch):
                    risk_signals.add(
                        "potential_breaking_api_change"
                    )

            if cls._has_auth_change(
                filename,
                patch,
            ):
                change_types.add("security")
                risk_signals.add(
                    "authentication_or_authorization_change"
                )

            if cls._is_dependency_file(filename):
                change_types.add("dependency")
                risk_signals.add(
                    "dependency_change"
                )

            if (
                cls._is_configuration_file(filename)
                and not cls._is_dependency_file(filename)
            ):
                change_types.add("configuration")
                risk_signals.add(
                    "configuration_change"
                )

            if cls._is_large_change(file):
                risk_signals.add(
                    "large_file_change"
                )

        if total_changes >= 500:
            risk_signals.add(
                "large_change"
            )

        return (
            sorted(change_types),
            sorted(risk_signals),
        )