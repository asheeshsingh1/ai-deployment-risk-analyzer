from pydantic import BaseModel


class PullRequestFile(BaseModel):
    filename: str
    status: str
    additions: int
    deletions: int
    changes: int
    patch: str | None = None


class PullRequest(BaseModel):
    number: int
    title: str
    body: str | None
    state: str
    base_branch: str
    head_branch: str
    head_sha: str
    files: list[PullRequestFile]