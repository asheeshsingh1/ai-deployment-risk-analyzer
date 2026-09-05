from enum import Enum

from pydantic import BaseModel, Field


class RiskLevel(str, Enum):
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"


class RiskFactor(BaseModel):
    name: str
    description: str
    score: int = Field(ge=0, le=100)


class RiskAssessment(BaseModel):
    service: str
    score: int = Field(ge=0, le=100)
    level: RiskLevel
    factors: list[RiskFactor]
    recommendation: str


class PRRiskAssessment(BaseModel):
    repository: str
    pull_request_number: int
    pull_request_title: str

    affected_services: list[str]

    change_types: list[str]
    risk_signals: list[str]

    files_changed: int
    lines_added: int
    lines_deleted: int

    service_assessments: list[RiskAssessment]

    overall_score: int = Field(ge=0, le=100)
    overall_level: RiskLevel
    recommendation: str