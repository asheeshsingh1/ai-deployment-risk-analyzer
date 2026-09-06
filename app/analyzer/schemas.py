from pydantic import BaseModel, Field

from app.scm.schemas import ChangedFile


class ChangeAnalysis(BaseModel):
    provider: str
    repository: str

    change_request_number: int

    files_changed: int
    lines_added: int
    lines_deleted: int

    changed_files: list[ChangedFile] = Field(default_factory=list)

    affected_services: list[str] = Field(default_factory=list)

    change_types: list[str] = Field(default_factory=list)

    risk_signals: list[str] = Field(default_factory=list)

    service_mapping_status: str
