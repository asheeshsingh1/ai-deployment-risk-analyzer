from typing import Any

import httpx

from app.scm.github.schemas import PullRequest, PullRequestFile


class GitHubClient:
    BASE_URL = "https://api.github.com"

    def __init__(self, token: str):
        self.token = token

    def _headers(self) -> dict[str, str]:
        return {
            "Authorization": f"Bearer {self.token}",
            "Accept": "application/vnd.github+json",
            "X-GitHub-Api-Version": "2022-11-28",
        }

    def get_pull_request(
        self,
        owner: str,
        repo: str,
        pull_number: int,
    ) -> PullRequest:
        url = f"{self.BASE_URL}/repos/" f"{owner}/{repo}/pulls/{pull_number}"

        response = httpx.get(
            url,
            headers=self._headers(),
            timeout=10.0,
        )

        response.raise_for_status()

        data: dict[str, Any] = response.json()

        files = self.get_pull_request_files(
            owner,
            repo,
            pull_number,
        )

        return PullRequest(
            number=data["number"],
            title=data["title"],
            body=data.get("body"),
            state=data["state"],
            base_branch=data["base"]["ref"],
            head_branch=data["head"]["ref"],
            head_sha=data["head"]["sha"],
            files=files,
        )

    def get_pull_request_files(
        self,
        owner: str,
        repo: str,
        pull_number: int,
    ) -> list[PullRequestFile]:
        url = f"{self.BASE_URL}/repos/" f"{owner}/{repo}/pulls/{pull_number}/files"

        response = httpx.get(
            url,
            headers=self._headers(),
            params={"per_page": 100},
            timeout=10.0,
        )

        response.raise_for_status()

        data: list[dict[str, Any]] = response.json()

        return [
            PullRequestFile(
                filename=file["filename"],
                status=file["status"],
                additions=file["additions"],
                deletions=file["deletions"],
                changes=file["changes"],
                patch=file.get("patch"),
            )
            for file in data
        ]
