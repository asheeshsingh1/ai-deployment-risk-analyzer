from pydantic import BaseModel, Field


class ChangedFile(BaseModel):
    filename: str
    status: str
    additions: int
    deletions: int


class ChangeAnalysis(BaseModel):
    repository: str
    pull_request_number: int

    files_changed: int
    lines_added: int
    lines_deleted: int

    changed_files: list[ChangedFile] = Field(
        default_factory=list
    )

    affected_services: list[str] = Field(
        default_factory=list
    )

    change_types: list[str] = Field(
        default_factory=list
    )

    risk_signals: list[str] = Field(
        default_factory=list
    )

    service_mapping_status: str