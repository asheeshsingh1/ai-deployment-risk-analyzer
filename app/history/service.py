from collections import Counter
from datetime import datetime, timedelta, timezone

from app.db.models import DeploymentStatus
from app.history.schemas import (
    DeploymentHistory,
    HistoricalIntelligence,
    IncidentHistory,
)
from app.risk.repository import RiskRepository


class HistoricalIntelligenceService:
    def __init__(self, repository: RiskRepository):
        self.repository = repository

    @staticmethod
    def _as_utc(
        value: datetime,
    ) -> datetime:
        if value.tzinfo is None:
            return value.replace(
                tzinfo=timezone.utc,
            )

        return value.astimezone(timezone.utc)

    @staticmethod
    def _deployment_history(
        deployments,
        days: int,
    ) -> DeploymentHistory:
        total = len(deployments)

        successful = sum(
            deployment.status == DeploymentStatus.SUCCESS for deployment in deployments
        )

        failed = sum(
            deployment.status == DeploymentStatus.FAILED for deployment in deployments
        )

        rolled_back = sum(
            deployment.status == DeploymentStatus.ROLLED_BACK
            for deployment in deployments
        )

        failure_rate = (failed + rolled_back) / total if total else 0.0

        rollback_rate = rolled_back / total if total else 0.0

        recent_cutoff = datetime.now(timezone.utc) - timedelta(days=min(days, 30))

        recent_deployments = sum(
            HistoricalIntelligenceService._as_utc(deployment.deployed_at)
            >= recent_cutoff
            for deployment in deployments
        )

        return DeploymentHistory(
            total_deployments=total,
            successful_deployments=successful,
            failed_deployments=failed,
            rolled_back_deployments=rolled_back,
            failure_rate=round(
                failure_rate,
                4,
            ),
            rollback_rate=round(
                rollback_rate,
                4,
            ),
            recent_deployments=recent_deployments,
        )

    @staticmethod
    def _incident_history(
        incidents,
        days: int,
    ) -> IncidentHistory:
        severity_counts = Counter(incident.severity.value for incident in incidents)

        recent_cutoff = datetime.now(timezone.utc) - timedelta(days=min(days, 30))

        recent_incidents = sum(
            HistoricalIntelligenceService._as_utc(incident.started_at) >= recent_cutoff
            for incident in incidents
        )

        return IncidentHistory(
            total_incidents=len(incidents),
            low_severity=severity_counts["low"],
            medium_severity=severity_counts["medium"],
            high_severity=severity_counts["high"],
            critical_severity=severity_counts["critical"],
            recent_incidents=recent_incidents,
        )

    @staticmethod
    def _build_evidence(
        deployments: DeploymentHistory,
        incidents: IncidentHistory,
    ) -> list[str]:
        evidence: list[str] = []

        if deployments.total_deployments == 0:
            evidence.append(
                "No deployment history is available "
                "for the selected historical window."
            )
        else:
            evidence.append(
                f"{deployments.total_deployments} deployments "
                "were recorded in the historical window."
            )

            if deployments.failure_rate > 0:
                evidence.append(
                    f"{deployments.failure_rate:.0%} of deployments "
                    "failed or were rolled back."
                )

            if deployments.rollback_rate > 0:
                evidence.append(
                    f"{deployments.rollback_rate:.0%} of deployments "
                    "were rolled back."
                )

            evidence.append(
                f"{deployments.recent_deployments} deployments "
                "occurred in the last 30 days."
            )

        if incidents.total_incidents == 0:
            evidence.append("No incidents were recorded " "in the historical window.")
        else:
            evidence.append(
                f"{incidents.total_incidents} incidents "
                "were recorded in the historical window."
            )

            if incidents.high_severity > 0:
                evidence.append(
                    f"{incidents.high_severity} high-severity "
                    "incidents were recorded."
                )

            if incidents.critical_severity > 0:
                evidence.append(
                    f"{incidents.critical_severity} critical-severity "
                    "incidents were recorded."
                )

            if incidents.recent_incidents > 0:
                evidence.append(
                    f"{incidents.recent_incidents} incidents "
                    "occurred in the last 30 days."
                )

        return evidence

    def analyze(
        self,
        service_id: int,
        service_name: str,
        days: int = 30,
    ) -> HistoricalIntelligence:
        deployments = self.repository.get_recent_deployments(
            service_id=service_id,
            days=days,
        )

        incidents = self.repository.get_recent_incidents(
            service_id=service_id,
            days=days,
        )

        deployment_history = self._deployment_history(
            deployments=deployments,
            days=days,
        )

        incident_history = self._incident_history(
            incidents=incidents,
            days=days,
        )

        evidence = self._build_evidence(
            deployments=deployment_history,
            incidents=incident_history,
        )

        return HistoricalIntelligence(
            service=service_name,
            window_days=days,
            deployments=deployment_history,
            incidents=incident_history,
            evidence=evidence,
        )
