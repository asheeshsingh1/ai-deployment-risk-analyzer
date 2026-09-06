from dataclasses import dataclass

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
    """
    Deterministic deployment risk engine.

    The engine combines:
    1. Historical operational evidence.
    2. Deterministic signals detected from the change.

    The engine owns the final score. AI components must never
    calculate or modify this score.
    """

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
                "Authentication or authorization behavior "
                "is being modified."
            ),
        ),
        RiskSignalRule(
            signal="database_change",
            score=20,
            name="database_change",
            description=(
                "The change modifies database schema, "
                "migrations, or persistence behavior."
            ),
        ),
        RiskSignalRule(
            signal="infrastructure_change",
            score=15,
            name="infrastructure_change",
            description=(
                "The change modifies deployment or "
                "infrastructure configuration."
            ),
        ),
        RiskSignalRule(
            signal="dependency_change",
            score=10,
            name="dependency_change",
            description=(
                "The change modifies application dependencies "
                "or dependency lock files."
            ),
        ),
        RiskSignalRule(
            signal="configuration_change",
            score=10,
            name="configuration_change",
            description=(
                "The change modifies application configuration."
            ),
        ),
        RiskSignalRule(
            signal="large_change",
            score=10,
            name="large_change",
            description=(
                "The change contains a large number of "
                "modified lines."
            ),
        ),
        RiskSignalRule(
            signal="large_file_change",
            score=5,
            name="large_file_change",
            description=(
                "At least one changed file contains a "
                "large number of modified lines."
            ),
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
                "Use a staged or canary deployment and "
                "closely monitor production metrics."
            )

        if level == RiskLevel.MEDIUM:
            return (
                "Use additional validation and monitor "
                "the deployment closely."
            )

        return (
            "Standard deployment is reasonable with "
            "normal production monitoring."
        )

    def _historical_factors(
        self,
        service_id: int,
    ) -> list[RiskFactor]:
        deployments = (
            self.repository.get_recent_deployments(
                service_id=service_id,
            )
        )

        incidents = (
            self.repository.get_recent_incidents(
                service_id=service_id,
            )
        )

        factors: list[RiskFactor] = []

        if not deployments:
            factors.append(
                RiskFactor(
                    name="insufficient_deployment_history",
                    description=(
                        "No recent deployment history is "
                        "available for this service."
                    ),
                    score=10,
                )
            )

        else:
            failed_or_rollback = sum(
                deployment.status
                in {
                    "failed",
                    "rolled_back",
                }
                for deployment in deployments
            )

            failure_rate = (
                failed_or_rollback
                / len(deployments)
            )

            if failure_rate >= 0.30:
                factors.append(
                    RiskFactor(
                        name="high_deployment_failure_rate",
                        description=(
                            f"{failure_rate:.0%} of recent "
                            "deployments failed or were rolled back."
                        ),
                        score=30,
                    )
                )

            elif failure_rate >= 0.15:
                factors.append(
                    RiskFactor(
                        name="elevated_deployment_failure_rate",
                        description=(
                            f"{failure_rate:.0%} of recent "
                            "deployments failed or were rolled back."
                        ),
                        score=15,
                    )
                )

        high_severity_incidents = sum(
            incident.severity
            in {
                "high",
                "critical",
            }
            for incident in incidents
        )

        if high_severity_incidents >= 2:
            factors.append(
                RiskFactor(
                    name="recent_high_severity_incidents",
                    description=(
                        f"{high_severity_incidents} high or "
                        "critical severity incidents occurred recently."
                    ),
                    score=30,
                )
            )

        elif high_severity_incidents == 1:
            factors.append(
                RiskFactor(
                    name="recent_high_severity_incident",
                    description=(
                        "A high-severity incident occurred recently."
                    ),
                    score=15,
                )
            )

        incident_count = len(incidents)

        if incident_count >= 4:
            factors.append(
                RiskFactor(
                    name="high_incident_volume",
                    description=(
                        f"{incident_count} incidents occurred "
                        "in the last 30 days."
                    ),
                    score=20,
                )
            )

        elif incident_count >= 2:
            factors.append(
                RiskFactor(
                    name="elevated_incident_volume",
                    description=(
                        f"{incident_count} incidents occurred "
                        "in the last 30 days."
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

        signal_set = set(risk_signals)

        for rule in self.SIGNAL_RULES:
            if rule.signal not in signal_set:
                continue

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
    ) -> RiskAssessment:
        factors = self._historical_factors(
            service_id=service_id,
        )

        factors.extend(
            self._change_signal_factors(
                risk_signals=risk_signals,
            )
        )

        score = min(
            100,
            sum(
                factor.score
                for factor in factors
            ),
        )

        level = self._risk_level(score)

        return RiskAssessment(
            service=service_name,
            score=score,
            level=level,
            factors=factors,
            recommendation=self._recommendation(
                level
            ),
        )