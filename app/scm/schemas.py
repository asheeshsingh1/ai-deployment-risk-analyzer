from pydantic import BaseModel


class ChangedFile(BaseModel):
    filename: str
    status: str
    additions: int
    deletions: int
    changes: int
    patch: str | None = None


class CodeChangeRequest(BaseModel):
    number: int
    title: str
    body: str | None
    state: str

    base_branch: str
    head_branch: str
    head_sha: str

    files: list[ChangedFile]