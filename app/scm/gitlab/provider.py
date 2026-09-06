from __future__ import annotations

from typing import Any
from urllib.parse import quote

import httpx

from app.scm.base import SCMProvider
from app.scm.exceptions import (
    SCMAuthenticationError,
    SCMNotFoundError,
    SCMRateLimitError,
    SCMRequestError,
)
from app.scm.schemas import ChangedFile, CodeChangeRequest


class GitLabProvider(SCMProvider):
    BASE_URL = "https://gitlab.com/api/v4"
    DEFAULT_TIMEOUT = 15.0
    PAGE_SIZE = 100

    def __init__(
        self,
        token: str,
        *,
        timeout: float = DEFAULT_TIMEOUT,
    ) -> None:
        self.token = token
        self.timeout = timeout

    def _headers(self) -> dict[str, str]:
        headers = {
            "Accept": "application/json",
        }

        if self.token:
            headers["PRIVATE-TOKEN"] = self.token

        return headers

    @staticmethod
    def _project_path(owner: str, repository: str) -> str:
        return quote(
            f"{owner}/{repository}",
            safe="",
        )

    def _request(
        self,
        method: str,
        path: str,
        *,
        params: dict[str, Any] | None = None,
        json: dict[str, Any] | None = None,
    ) -> httpx.Response:
        url = f"{self.BASE_URL}{path}"

        try:
            response = httpx.request(
                method,
                url,
                headers=self._headers(),
                params=params,
                json=json,
                timeout=self.timeout,
            )
        except httpx.TimeoutException as exc:
            raise SCMRequestError(
                "GitLab request timed out.",
                provider="gitlab",
            ) from exc
        except httpx.RequestError as exc:
            raise SCMRequestError(
                f"GitLab request failed: {exc}",
                provider="gitlab",
            ) from exc

        if response.status_code in {401, 403}:
            raise SCMAuthenticationError(
                "GitLab authentication or authorization failed.",
                provider="gitlab",
                status_code=response.status_code,
            )

        if response.status_code == 404:
            raise SCMNotFoundError(
                "GitLab resource was not found.",
                provider="gitlab",
                status_code=response.status_code,
            )

        if response.status_code == 429:
            raise SCMRateLimitError(
                "GitLab API rate limit exceeded.",
                provider="gitlab",
                status_code=response.status_code,
            )

        if response.is_error:
            detail = self._response_detail(response)

            raise SCMRequestError(
                f"GitLab API request failed with status "
                f"{response.status_code}: {detail}",
                provider="gitlab",
                status_code=response.status_code,
            )

        return response

    @staticmethod
    def _response_detail(response: httpx.Response) -> str:
        try:
            payload = response.json()
        except ValueError:
            return response.text[:500]

        if isinstance(payload, dict):
            message = payload.get("message")
            if message:
                return str(message)

        return response.text[:500]

    def _get_all_changes(
        self,
        owner: str,
        repository: str,
        change_number: int,
    ) -> list[ChangedFile]:
        project = self._project_path(owner, repository)

        files: list[ChangedFile] = []
        page = 1

        while True:
            response = self._request(
                "GET",
                f"/projects/{project}/merge_requests/{change_number}/changes",
                params={
                    "per_page": self.PAGE_SIZE,
                    "page": page,
                },
            )

            payload = response.json()

            if not isinstance(payload, dict):
                raise SCMRequestError(
                    "GitLab returned an unexpected merge-request " "changes response.",
                    provider="gitlab",
                    status_code=response.status_code,
                )

            changes = payload.get("changes", [])

            if not isinstance(changes, list):
                raise SCMRequestError(
                    "GitLab returned an invalid changes collection.",
                    provider="gitlab",
                    status_code=response.status_code,
                )

            if not changes:
                break

            for item in changes:
                new_path = item.get("new_path")
                old_path = item.get("old_path")

                filename = new_path or old_path

                if not filename:
                    continue

                files.append(
                    ChangedFile(
                        filename=filename,
                        status=self._change_status(item),
                        additions=self._parse_diff_additions(item.get("diff", "")),
                        deletions=self._parse_diff_deletions(item.get("diff", "")),
                        changes=(
                            self._parse_diff_additions(item.get("diff", ""))
                            + self._parse_diff_deletions(item.get("diff", ""))
                        ),
                        patch=item.get("diff"),
                    )
                )

            if len(changes) < self.PAGE_SIZE:
                break

            page += 1

        return files

    @staticmethod
    def _change_status(item: dict[str, Any]) -> str:
        if item.get("new_file"):
            return "added"

        if item.get("deleted_file"):
            return "deleted"

        if item.get("renamed_file"):
            return "renamed"

        return "modified"

    @staticmethod
    def _parse_diff_additions(diff: str) -> int:
        if not diff:
            return 0

        additions = 0

        for line in diff.splitlines():
            if line.startswith("+") and not line.startswith("+++"):
                additions += 1

        return additions

    @staticmethod
    def _parse_diff_deletions(diff: str) -> int:
        if not diff:
            return 0

        deletions = 0

        for line in diff.splitlines():
            if line.startswith("-") and not line.startswith("---"):
                deletions += 1

        return deletions

    def get_change_request(
        self,
        owner: str,
        repository: str,
        change_number: int,
    ) -> CodeChangeRequest:
        project = self._project_path(owner, repository)

        response = self._request(
            "GET",
            f"/projects/{project}/merge_requests/{change_number}",
        )

        payload = response.json()

        files = self._get_all_changes(
            owner=owner,
            repository=repository,
            change_number=change_number,
        )

        stats = payload.get("changes_count")

        try:
            int(stats)
        except (TypeError, ValueError):
            pass

        return CodeChangeRequest(
            number=payload["iid"],
            title=payload["title"],
            body=payload.get("description"),
            state=payload["state"],
            base_branch=payload["target_branch"],
            head_branch=payload["source_branch"],
            head_sha=payload["sha"],
            files=files,
        )

    def add_change_request_comment(
        self,
        owner: str,
        repository: str,
        change_number: int,
        body: str,
    ) -> None:
        project = self._project_path(owner, repository)

        self._request(
            "POST",
            f"/projects/{project}/merge_requests/{change_number}/notes",
            json={"body": body},
        )
