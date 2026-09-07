from dataclasses import dataclass
from urllib.parse import urlparse


class ChangeRequestUrlError(ValueError):
    """Raised when a change request URL cannot be parsed."""


@dataclass(frozen=True)
class ParsedChangeRequestUrl:
    provider: str
    owner: str
    repository: str
    change_number: int


class ChangeRequestUrlParser:
    """
    Parses GitHub Pull Request and GitLab Merge Request URLs.

    Supported GitHub format:

        https://github.com/<owner>/<repository>/pull/<number>

    Supported GitLab format:

        https://gitlab.com/<namespace>/<project>/-/merge_requests/<iid>

    GitLab namespaces may contain nested groups:

        https://gitlab.com/company/platform/project/-/merge_requests/42
    """

    GITHUB_HOST = "github.com"
    GITLAB_HOST = "gitlab.com"

    @classmethod
    def parse(
        cls,
        change_request_url: str,
    ) -> ParsedChangeRequestUrl:
        if not change_request_url:
            raise ChangeRequestUrlError("Change request URL is required.")

        url = change_request_url.strip()

        if not url:
            raise ChangeRequestUrlError("Change request URL is required.")

        parsed = urlparse(url)

        if parsed.scheme not in {"http", "https"}:
            raise ChangeRequestUrlError("Change request URL must use http or https.")

        hostname = (parsed.hostname or "").lower().rstrip(".")

        if hostname == cls.GITHUB_HOST:
            return cls._parse_github(parsed.path)

        if hostname == cls.GITLAB_HOST:
            return cls._parse_gitlab(parsed.path)

        raise ChangeRequestUrlError(
            "Unsupported SCM host. " "Only GitHub and GitLab URLs are supported."
        )

    @classmethod
    def _parse_github(
        cls,
        path: str,
    ) -> ParsedChangeRequestUrl:
        parts = cls._path_parts(path)

        if len(parts) != 4:
            raise ChangeRequestUrlError(
                "Invalid GitHub Pull Request URL. "
                "Expected /<owner>/<repository>/pull/<number>."
            )

        owner, repository, resource, change_number = parts

        if resource != "pull":
            raise ChangeRequestUrlError(
                "Invalid GitHub URL. " "Expected a Pull Request URL."
            )

        number = cls._parse_change_number(change_number)

        return ParsedChangeRequestUrl(
            provider="github",
            owner=owner,
            repository=repository.removesuffix(".git"),
            change_number=number,
        )

    @classmethod
    def _parse_gitlab(
        cls,
        path: str,
    ) -> ParsedChangeRequestUrl:
        parts = cls._path_parts(path)

        try:
            marker_index = parts.index("-")
        except ValueError as exc:
            raise ChangeRequestUrlError(
                "Invalid GitLab Merge Request URL. "
                "Expected /<namespace>/<project>/-/merge_requests/<iid>."
            ) from exc

        namespace_parts = parts[:marker_index]
        remaining_parts = parts[marker_index + 1 :]

        if len(namespace_parts) < 2:
            raise ChangeRequestUrlError(
                "Invalid GitLab Merge Request URL. "
                "A namespace and project are required."
            )

        if len(remaining_parts) != 2:
            raise ChangeRequestUrlError(
                "Invalid GitLab Merge Request URL. "
                "Expected /<namespace>/<project>/-/merge_requests/<iid>."
            )

        resource, change_number = remaining_parts

        if resource != "merge_requests":
            raise ChangeRequestUrlError(
                "Invalid GitLab URL. " "Expected a Merge Request URL."
            )

        number = cls._parse_change_number(change_number)

        repository = namespace_parts[-1].removesuffix(".git")
        owner = "/".join(namespace_parts[:-1])

        return ParsedChangeRequestUrl(
            provider="gitlab",
            owner=owner,
            repository=repository,
            change_number=number,
        )

    @staticmethod
    def _path_parts(path: str) -> list[str]:
        return [part for part in path.strip("/").split("/") if part]

    @staticmethod
    def _parse_change_number(
        value: str,
    ) -> int:
        if not value.isdigit():
            raise ChangeRequestUrlError(
                "Change request number must be a positive integer."
            )

        number = int(value)

        if number <= 0:
            raise ChangeRequestUrlError(
                "Change request number must be a positive integer."
            )

        return number
