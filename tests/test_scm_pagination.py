import httpx

from app.scm.github.provider import GitHubProvider
from app.scm.gitlab.provider import GitLabProvider


def test_gitlab_deleted_file_uses_old_path():
    item = {
        "old_path": "app/old.py",
        "new_path": "app/old.py",
        "new_file": False,
        "deleted_file": True,
        "renamed_file": False,
        "diff": "@@\n-old",
    }

    assert GitLabProvider._change_status(item) == "deleted"


def test_gitlab_renamed_file_uses_new_path():
    item = {
        "old_path": "app/old.py",
        "new_path": "app/new.py",
        "new_file": False,
        "deleted_file": False,
        "renamed_file": True,
        "diff": "@@",
    }

    assert GitLabProvider._change_status(item) == "renamed"


def test_github_changed_files_are_paginated(monkeypatch):
    provider = GitHubProvider(token="test-token")

    calls = []

    def fake_request(method, url, **kwargs):
        page = kwargs["params"]["page"]
        calls.append(page)

        if page == 1:
            files = [
                {
                    "filename": f"app/file{i}.py",
                    "status": "modified",
                    "additions": 1,
                    "deletions": 1,
                    "changes": 2,
                    "patch": "@@",
                }
                for i in range(100)
            ]
        else:
            files = [
                {
                    "filename": "app/file100.py",
                    "status": "added",
                    "additions": 5,
                    "deletions": 0,
                    "changes": 5,
                    "patch": "@@",
                }
            ]

        return httpx.Response(
            200,
            json=files,
            request=httpx.Request(method, url),
        )

    monkeypatch.setattr(provider, "_request", fake_request)

    files = provider._get_all_files(
        owner="owner",
        repository="repo",
        change_number=1,
    )

    assert len(files) == 101
    assert calls == [1, 2]


def test_gitlab_changed_files_are_paginated(monkeypatch):
    provider = GitLabProvider(token="test-token")

    calls = []

    def fake_request(method, url, **kwargs):
        page = kwargs["params"]["page"]
        calls.append(page)

        if page == 1:
            changes = [
                {
                    "old_path": f"app/file{i}.py",
                    "new_path": f"app/file{i}.py",
                    "new_file": False,
                    "deleted_file": False,
                    "renamed_file": False,
                    "diff": "@@ -1 +1 @@\n-old\n+new",
                }
                for i in range(100)
            ]
        else:
            changes = [
                {
                    "old_path": "app/file100.py",
                    "new_path": "app/file100.py",
                    "new_file": True,
                    "deleted_file": False,
                    "renamed_file": False,
                    "diff": "@@\n+new",
                }
            ]

        return httpx.Response(
            200,
            json={"changes": changes},
            request=httpx.Request(method, url),
        )

    monkeypatch.setattr(provider, "_request", fake_request)

    files = provider._get_all_changes(
        owner="owner",
        repository="repo",
        change_number=1,
    )

    assert len(files) == 101
    assert files[-1].filename == "app/file100.py"
    assert calls == [1, 2]
