from datetime import datetime, timedelta, timezone

from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.db.models import (
    Deployment,
    DeploymentStatus,
    Incident,
    IncidentSeverity,
    Service,
)


class RiskRepository:
    def __init__(self, db: Session):
        self.db = db

    def get_service(self, service_name: str) -> Service | None:
        statement = select(Service).where(
            Service.name == service_name
        )

        return self.db.scalar(statement)

    def get_recent_deployments(
        self,
        service_id: int,
        days: int = 30,
    ) -> list[Deployment]:
        since = datetime.now(timezone.utc) - timedelta(days=days)

        statement = (
            select(Deployment)
            .where(
                Deployment.service_id == service_id,
                Deployment.deployed_at >= since,
            )
            .order_by(Deployment.deployed_at.desc())
        )

        return list(self.db.scalars(statement).all())

    def get_recent_incidents(
        self,
        service_id: int,
        days: int = 30,
    ) -> list[Incident]:
        since = datetime.now(timezone.utc) - timedelta(days=days)

        statement = (
            select(Incident)
            .where(
                Incident.service_id == service_id,
                Incident.started_at >= since,
            )
            .order_by(Incident.started_at.desc())
        )

        return list(self.db.scalars(statement).all())

    def get_deployment_failure_rate(
        self,
        service_id: int,
        days: int = 30,
    ) -> float:
        deployments = self.get_recent_deployments(
            service_id,
            days,
        )

        if not deployments:
            return 0.0

        failed = sum(
            deployment.status
            in {
                DeploymentStatus.FAILED,
                DeploymentStatus.ROLLED_BACK,
            }
            for deployment in deployments
        )

        return failed / len(deployments)

    def get_high_severity_incident_count(
        self,
        service_id: int,
        days: int = 30,
    ) -> int:
        incidents = self.get_recent_incidents(
            service_id,
            days,
        )

        high_severity = {
            IncidentSeverity.HIGH,
            IncidentSeverity.CRITICAL,
        }

        return sum(
            incident.severity in high_severity
            for incident in incidents
        )