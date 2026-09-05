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