from __future__ import annotations

from typing import Any

import httpx

from app.scm.base import SCMProvider
from app.scm.exceptions import (
    SCMAuthenticationError,
    SCMNotFoundError,
    SCMRateLimitError,
    SCMRequestError,
)
from app.scm.schemas import ChangedFile, CodeChangeRequest


class GitHubProvider(SCMProvider):
    BASE_URL = "https://api.github.com"
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
            "Accept": "application/vnd.github+json",
            "X-GitHub-Api-Version": "2022-11-28",
        }

        if self.token:
            headers["Authorization"] = f"Bearer {self.token}"

        return headers

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
                "GitHub request timed out.",
                provider="github",
            ) from exc
        except httpx.RequestError as exc:
            raise SCMRequestError(
                f"GitHub request failed: {exc}",
                provider="github",
            ) from exc

        if response.status_code in {401, 403}:
            if (
                response.status_code == 403
                and response.headers.get("X-RateLimit-Remaining") == "0"
            ):
                raise SCMRateLimitError(
                    "GitHub API rate limit exceeded.",
                    provider="github",
                    status_code=response.status_code,
                )

            raise SCMAuthenticationError(
                "GitHub authentication or authorization failed.",
                provider="github",
                status_code=response.status_code,
            )

        if response.status_code == 404:
            raise SCMNotFoundError(
                "GitHub resource was not found.",
                provider="github",
                status_code=response.status_code,
            )

        if response.status_code == 429:
            raise SCMRateLimitError(
                "GitHub API rate limit exceeded.",
                provider="github",
                status_code=response.status_code,
            )

        if response.is_error:
            detail = self._response_detail(response)

            raise SCMRequestError(
                f"GitHub API request failed with status "
                f"{response.status_code}: {detail}",
                provider="github",
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

    def _get_all_files(
        self,
        owner: str,
        repository: str,
        change_number: int,
    ) -> list[ChangedFile]:
        files: list[ChangedFile] = []
        page = 1

        while True:
            response = self._request(
                "GET",
                f"/repos/{owner}/{repository}/pulls/{change_number}/files",
                params={
                    "per_page": self.PAGE_SIZE,
                    "page": page,
                },
            )

            payload = response.json()

            if not isinstance(payload, list):
                raise SCMRequestError(
                    "GitHub returned an unexpected changed-files response.",
                    provider="github",
                    status_code=response.status_code,
                )

            if not payload:
                break

            for item in payload:
                files.append(
                    ChangedFile(
                        filename=item["filename"],
                        status=item["status"],
                        additions=item.get("additions", 0),
                        deletions=item.get("deletions", 0),
                        changes=item.get("changes", 0),
                        patch=item.get("patch"),
                    )
                )

            if len(payload) < self.PAGE_SIZE:
                break

            page += 1

        return files

    def get_change_request(
        self,
        owner: str,
        repository: str,
        change_number: int,
    ) -> CodeChangeRequest:
        response = self._request(
            "GET",
            f"/repos/{owner}/{repository}/pulls/{change_number}",
        )

        payload = response.json()

        files = self._get_all_files(
            owner=owner,
            repository=repository,
            change_number=change_number,
        )

        return CodeChangeRequest(
            number=payload["number"],
            title=payload["title"],
            body=payload.get("body"),
            state=payload["state"],
            base_branch=payload["base"]["ref"],
            head_branch=payload["head"]["ref"],
            head_sha=payload["head"]["sha"],
            files=files,
        )

    def add_change_request_comment(
        self,
        owner: str,
        repository: str,
        change_number: int,
        body: str,
    ) -> None:
        self._request(
            "POST",
            f"/repos/{owner}/{repository}/issues/{change_number}/comments",
            json={"body": body},
        )
