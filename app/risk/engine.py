from dataclasses import dataclass

from app.history.schemas import HistoricalIntelligence
from app.risk.schemas import (
    RiskAssessment,
    RiskFactor,
    RiskLevel,
)


@dataclass(frozen=True)
class RiskSignalRule:
    signal: str
    score: int
    name: str
    description: str


class RiskEngine:
    SIGNAL_RULES = (
        RiskSignalRule(
            signal="potential_breaking_api_change",
            score=25,
            name="potential_breaking_api_change",
            description=(
                "The change may alter an API contract "
                "in a way that could affect consumers."
            ),
        ),
        RiskSignalRule(
            signal="authentication_or_authorization_change",
            score=25,
            name="authentication_or_authorization_change",
            description=(
                "Authentication or authorization behavior " "is being modified."
            ),
        ),
        RiskSignalRule(
            signal="database_change",
            score=20,
            name="database_change",
            description=(
                "Database schema or persistence behavior " "is being modified."
            ),
        ),
        RiskSignalRule(
            signal="infrastructure_change",
            score=15,
            name="infrastructure_change",
            description=(
                "Infrastructure or deployment configuration " "is being modified."
            ),
        ),
        RiskSignalRule(
            signal="dependency_change",
            score=10,
            name="dependency_change",
            description=("Application dependencies are being modified."),
        ),
        RiskSignalRule(
            signal="configuration_change",
            score=10,
            name="configuration_change",
            description=("Runtime configuration is being modified."),
        ),
        RiskSignalRule(
            signal="large_change",
            score=10,
            name="large_change",
            description=("The change contains a large number " "of modified lines."),
        ),
        RiskSignalRule(
            signal="large_file_change",
            score=5,
            name="large_file_change",
            description=("At least one changed file contains " "a large modification."),
        ),
    )

    def __init__(self, repository):
        self.repository = repository

    @staticmethod
    def _risk_level(score: int) -> RiskLevel:
        if score >= 75:
            return RiskLevel.CRITICAL

        if score >= 50:
            return RiskLevel.HIGH

        if score >= 25:
            return RiskLevel.MEDIUM

        return RiskLevel.LOW

    @staticmethod
    def _recommendation(
        level: RiskLevel,
    ) -> str:
        if level == RiskLevel.CRITICAL:
            return (
                "Block the deployment pending manual review, "
                "additional validation, and a controlled rollout."
            )

        if level == RiskLevel.HIGH:
            return (
                "Use a staged or canary deployment with "
                "active monitoring and rollback readiness."
            )

        if level == RiskLevel.MEDIUM:
            return (
                "Perform additional validation and deploy " "with enhanced monitoring."
            )

        return "Proceed with the standard deployment process " "and normal monitoring."

    def _historical_factors(
        self,
        historical: HistoricalIntelligence,
    ) -> list[RiskFactor]:
        factors: list[RiskFactor] = []

        deployments = historical.deployments
        incidents = historical.incidents

        if deployments.total_deployments == 0:
            factors.append(
                RiskFactor(
                    name="insufficient_deployment_history",
                    description=(
                        "No deployments were recorded in the " "historical window."
                    ),
                    score=10,
                )
            )

        elif deployments.failure_rate >= 0.30:
            factors.append(
                RiskFactor(
                    name="high_deployment_failure_rate",
                    description=(
                        f"{deployments.failure_rate:.0%} of recent "
                        "deployments failed or were rolled back."
                    ),
                    score=30,
                )
            )

        elif deployments.failure_rate >= 0.15:
            factors.append(
                RiskFactor(
                    name="elevated_deployment_failure_rate",
                    description=(
                        f"{deployments.failure_rate:.0%} of recent "
                        "deployments failed or were rolled back."
                    ),
                    score=15,
                )
            )

        if incidents.critical_severity >= 1:
            factors.append(
                RiskFactor(
                    name="critical_incident_history",
                    description=(
                        f"{incidents.critical_severity} "
                        "critical-severity incidents occurred "
                        "in the historical window."
                    ),
                    score=30,
                )
            )

        elif incidents.high_severity >= 2:
            factors.append(
                RiskFactor(
                    name="multiple_high_severity_incidents",
                    description=(
                        f"{incidents.high_severity} high-severity "
                        "incidents occurred in the historical window."
                    ),
                    score=30,
                )
            )

        elif incidents.high_severity == 1:
            factors.append(
                RiskFactor(
                    name="recent_high_severity_incident",
                    description=(
                        "A high-severity incident occurred " "in the historical window."
                    ),
                    score=15,
                )
            )

        if incidents.total_incidents >= 4:
            factors.append(
                RiskFactor(
                    name="high_incident_volume",
                    description=(
                        f"{incidents.total_incidents} incidents "
                        "occurred in the historical window."
                    ),
                    score=20,
                )
            )

        elif incidents.total_incidents >= 2:
            factors.append(
                RiskFactor(
                    name="elevated_incident_volume",
                    description=(
                        f"{incidents.total_incidents} incidents "
                        "occurred in the historical window."
                    ),
                    score=10,
                )
            )

        if incidents.recent_incidents >= 2:
            factors.append(
                RiskFactor(
                    name="recent_incident_activity",
                    description=(
                        f"{incidents.recent_incidents} incidents "
                        "occurred in the last 30 days."
                    ),
                    score=10,
                )
            )

        return factors

    def _change_signal_factors(
        self,
        risk_signals: list[str],
    ) -> list[RiskFactor]:
        factors: list[RiskFactor] = []

        for rule in self.SIGNAL_RULES:
            if rule.signal in risk_signals:
                factors.append(
                    RiskFactor(
                        name=rule.name,
                        description=rule.description,
                        score=rule.score,
                    )
                )

        return factors

    def assess(
        self,
        service_name: str,
        service_id: int,
        risk_signals: list[str],
        historical_intelligence: HistoricalIntelligence,
    ) -> RiskAssessment:
        factors = self._historical_factors(
            historical=historical_intelligence,
        )

        factors.extend(
            self._change_signal_factors(
                risk_signals=risk_signals,
            )
        )

        score = min(
            100,
            sum(factor.score for factor in factors),
        )

        level = self._risk_level(score)

        return RiskAssessment(
            service=service_name,
            score=score,
            level=level,
            factors=factors,
            recommendation=self._recommendation(level),
            historical_intelligence=(historical_intelligence),
        )
