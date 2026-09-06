from datetime import datetime

from pydantic import BaseModel, Field

from app.db.models import DeploymentStatus, IncidentSeverity


class DeploymentHistory(BaseModel):
    total_deployments: int = Field(ge=0)
    successful_deployments: int = Field(ge=0)
    failed_deployments: int = Field(ge=0)
    rolled_back_deployments: int = Field(ge=0)
    failure_rate: float = Field(ge=0.0, le=1.0)
    rollback_rate: float = Field(ge=0.0, le=1.0)
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
    evidence: list[str] = Field(default_factory=list)


class DeploymentIngestionRequest(BaseModel):
    repository_id: int = Field(gt=0)
    service_id: int = Field(gt=0)

    commit_sha: str = Field(
        min_length=1,
        max_length=64,
    )

    status: DeploymentStatus
    deployed_at: datetime


class DeploymentIngestionResponse(BaseModel):
    id: int
    repository_id: int
    service_id: int
    commit_sha: str
    status: DeploymentStatus
    deployed_at: datetime
    created: bool


class IncidentIngestionRequest(BaseModel):
    service_id: int = Field(gt=0)

    deployment_id: int | None = Field(
        default=None,
        gt=0,
    )

    title: str = Field(
        min_length=1,
        max_length=255,
    )

    description: str = Field(
        min_length=1,
    )

    severity: IncidentSeverity
    started_at: datetime
    resolved_at: datetime | None = None


class IncidentIngestionResponse(BaseModel):
    id: int
    service_id: int
    deployment_id: int | None
    title: str
    description: str
    severity: IncidentSeverity
    started_at: datetime
    resolved_at: datetime | None
    created: bool
