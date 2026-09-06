from typing import Any

import httpx

from app.scm.base import SCMProvider
from app.scm.schemas import (
    ChangedFile,
    CodeChangeRequest,
)


class GitLabProvider(SCMProvider):
    BASE_URL = "https://gitlab.com/api/v4"

    def __init__(self, token: str):
        self.token = token

    def _headers(self) -> dict[str, str]:
        return {
            "PRIVATE-TOKEN": self.token,
        }

    @staticmethod
    def _project_id(
        owner: str,
        repository: str,
    ) -> str:
        return f"{owner}%2F{repository}"

    def get_change_request(
        self,
        owner: str,
        repository: str,
        change_number: int,
    ) -> CodeChangeRequest:
        project_id = self._project_id(
            owner,
            repository,
        )

        url = (
            f"{self.BASE_URL}/projects/"
            f"{project_id}/merge_requests/"
            f"{change_number}"
        )

        response = httpx.get(
            url,
            headers=self._headers(),
            timeout=10.0,
        )

        response.raise_for_status()

        data: dict[str, Any] = response.json()

        files = self._get_files(
            project_id=project_id,
            change_number=change_number,
        )

        return CodeChangeRequest(
            number=data["iid"],
            title=data["title"],
            body=data.get("description"),
            state=data["state"],
            base_branch=data["target_branch"],
            head_branch=data["source_branch"],
            head_sha=data["sha"],
            files=files,
        )

    def _get_files(
        self,
        project_id: str,
        change_number: int,
    ) -> list[ChangedFile]:
        url = (
            f"{self.BASE_URL}/projects/"
            f"{project_id}/merge_requests/"
            f"{change_number}/changes"
        )

        response = httpx.get(
            url,
            headers=self._headers(),
            timeout=10.0,
        )

        response.raise_for_status()

        data: dict[str, Any] = response.json()

        changes = data.get("changes", [])

        return [self._build_changed_file(change) for change in changes]

    @classmethod
    def _build_changed_file(
        cls,
        change: dict[str, Any],
    ) -> ChangedFile:
        diff = change.get("diff") or ""

        additions, deletions = cls._count_diff_lines(diff)

        return ChangedFile(
            filename=change["new_path"],
            status=cls._get_file_status(change),
            additions=additions,
            deletions=deletions,
            changes=additions + deletions,
            patch=diff,
        )

    @staticmethod
    def _count_diff_lines(
        diff: str,
    ) -> tuple[int, int]:
        additions = 0
        deletions = 0

        for line in diff.splitlines():
            if line.startswith("+++"):
                continue

            if line.startswith("---"):
                continue

            if line.startswith("+"):
                additions += 1

            elif line.startswith("-"):
                deletions += 1

        return additions, deletions

    @staticmethod
    def _get_file_status(
        change: dict[str, Any],
    ) -> str:
        if change.get("new_file"):
            return "added"

        if change.get("deleted_file"):
            return "deleted"

        if change.get("renamed_file"):
            return "renamed"

        return "modified"

    def add_change_request_comment(
        self,
        owner: str,
        repository: str,
        change_number: int,
        body: str,
    ) -> None:
        project_id = self._project_id(
            owner,
            repository,
        )

        url = (
            f"{self.BASE_URL}/projects/"
            f"{project_id}/merge_requests/"
            f"{change_number}/notes"
        )

        response = httpx.post(
            url,
            headers=self._headers(),
            data={"body": body},
            timeout=10.0,
        )

        response.raise_for_status()
