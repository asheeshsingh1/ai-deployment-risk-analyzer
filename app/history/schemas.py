from pydantic import BaseModel, Field


class DeploymentHistory(BaseModel):
    total_deployments: int = Field(ge=0)
    successful_deployments: int = Field(ge=0)
    failed_deployments: int = Field(ge=0)
    rolled_back_deployments: int = Field(ge=0)

    failure_rate: float = Field(
        ge=0.0,
        le=1.0,
    )

    rollback_rate: float = Field(
        ge=0.0,
        le=1.0,
    )

    recent_deployments: int = Field(ge=0)


class IncidentHistory(BaseModel):
    total_incidents: int = Field(ge=0)

    low_severity: int = Field(ge=0)
    medium_severity: int = Field(ge=0)
    high_severity: int = Field(ge=0)
    critical_severity: int = Field(ge=0)

    recent_incidents: int = Field(ge=0)


class HistoricalIntelligence(BaseModel):
    service: str

    window_days: int = Field(gt=0)

    deployments: DeploymentHistory
    incidents: IncidentHistory

    evidence: list[str] = Field(
        default_factory=list,
    )
