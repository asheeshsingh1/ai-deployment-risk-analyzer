from typing import Any

import httpx

from app.scm.base import SCMProvider
from app.scm.schemas import (
    ChangedFile,
    CodeChangeRequest,
)


class GitHubProvider(SCMProvider):
    BASE_URL = "https://api.github.com"

    def __init__(self, token: str):
        self.token = token

    def _headers(self) -> dict[str, str]:
        return {
            "Authorization": f"Bearer {self.token}",
            "Accept": "application/vnd.github+json",
            "X-GitHub-Api-Version": "2022-11-28",
        }

    def get_change_request(
        self,
        owner: str,
        repository: str,
        change_number: int,
    ) -> CodeChangeRequest:
        pull_url = (
            f"{self.BASE_URL}/repos/" f"{owner}/{repository}/pulls/" f"{change_number}"
        )

        response = httpx.get(
            pull_url,
            headers=self._headers(),
            timeout=10.0,
        )

        response.raise_for_status()

        data: dict[str, Any] = response.json()

        files = self._get_files(
            owner=owner,
            repository=repository,
            change_number=change_number,
        )

        return CodeChangeRequest(
            number=data["number"],
            title=data["title"],
            body=data.get("body"),
            state=data["state"],
            base_branch=data["base"]["ref"],
            head_branch=data["head"]["ref"],
            head_sha=data["head"]["sha"],
            files=files,
        )

    def _get_files(
        self,
        owner: str,
        repository: str,
        change_number: int,
    ) -> list[ChangedFile]:
        url = (
            f"{self.BASE_URL}/repos/"
            f"{owner}/{repository}/pulls/"
            f"{change_number}/files"
        )

        response = httpx.get(
            url,
            headers=self._headers(),
            params={"per_page": 100},
            timeout=10.0,
        )

        response.raise_for_status()

        data: list[dict[str, Any]] = response.json()

        return [
            ChangedFile(
                filename=file["filename"],
                status=file["status"],
                additions=file["additions"],
                deletions=file["deletions"],
                changes=file["changes"],
                patch=file.get("patch"),
            )
            for file in data
        ]

    def add_change_request_comment(
        self,
        owner: str,
        repository: str,
        change_number: int,
        body: str,
    ) -> None:
        url = (
            f"{self.BASE_URL}/repos/"
            f"{owner}/{repository}/issues/"
            f"{change_number}/comments"
        )

        response = httpx.post(
            url,
            headers=self._headers(),
            json={"body": body},
            timeout=10.0,
        )

        response.raise_for_status()
