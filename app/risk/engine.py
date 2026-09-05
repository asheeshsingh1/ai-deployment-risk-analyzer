from sqlalchemy.orm import Session

from app.risk.repository import RiskRepository
from app.risk.schemas import (
    RiskAssessment,
    RiskFactor,
    RiskLevel,
)


class RiskEngine:
    def __init__(self, db: Session):
        self.repository = RiskRepository(db)

    def assess(
        self,
        service_name: str,
    ) -> RiskAssessment:
        service = self.repository.get_service(service_name)

        if service is None:
            raise ValueError(
                f"Service '{service_name}' not found"
            )

        deployments = self.repository.get_recent_deployments(
            service.id
        )

        incidents = self.repository.get_recent_incidents(
            service.id
        )

        failure_rate = self.repository.get_deployment_failure_rate(
            service.id
        )

        high_severity_incidents = (
            self.repository.get_high_severity_incident_count(
                service.id
            )
        )

        factors: list[RiskFactor] = []

        score = 0

        # ---------------------------------------------------------
        # Deployment failure risk
        # ---------------------------------------------------------

        if failure_rate >= 0.30:
            factor_score = 30

            factors.append(
                RiskFactor(
                    name="high_deployment_failure_rate",
                    description=(
                        f"{failure_rate:.0%} of recent deployments "
                        "failed or were rolled back."
                    ),
                    score=factor_score,
                )
            )

            score += factor_score

        elif failure_rate >= 0.15:
            factor_score = 15

            factors.append(
                RiskFactor(
                    name="elevated_deployment_failure_rate",
                    description=(
                        f"{failure_rate:.0%} of recent deployments "
                        "failed or were rolled back."
                    ),
                    score=factor_score,
                )
            )

            score += factor_score

        # ---------------------------------------------------------
        # Incident risk
        # ---------------------------------------------------------

        if high_severity_incidents >= 2:
            factor_score = 30

            factors.append(
                RiskFactor(
                    name="recent_high_severity_incidents",
                    description=(
                        f"{high_severity_incidents} high-severity "
                        "incidents occurred recently."
                    ),
                    score=factor_score,
                )
            )

            score += factor_score

        elif high_severity_incidents == 1:
            factor_score = 15

            factors.append(
                RiskFactor(
                    name="recent_high_severity_incident",
                    description=(
                        "A high-severity incident occurred "
                        "recently."
                    ),
                    score=factor_score,
                )
            )

            score += factor_score

        # ---------------------------------------------------------
        # Incident volume
        # ---------------------------------------------------------

        if len(incidents) >= 4:
            factor_score = 20

            factors.append(
                RiskFactor(
                    name="high_incident_volume",
                    description=(
                        f"{len(incidents)} incidents occurred "
                        "in the last 30 days."
                    ),
                    score=factor_score,
                )
            )

            score += factor_score

        elif len(incidents) >= 2:
            factor_score = 10

            factors.append(
                RiskFactor(
                    name="elevated_incident_volume",
                    description=(
                        f"{len(incidents)} incidents occurred "
                        "in the last 30 days."
                    ),
                    score=factor_score,
                )
            )

            score += factor_score

        # ---------------------------------------------------------
        # No historical data
        # ---------------------------------------------------------

        if not deployments:
            factors.append(
                RiskFactor(
                    name="insufficient_deployment_history",
                    description=(
                        "No recent deployment history is available "
                        "for this service."
                    ),
                    score=10,
                )
            )

            score += 10

        # ---------------------------------------------------------
        # Normalize score
        # ---------------------------------------------------------

        score = min(score, 100)

        level = self._get_risk_level(score)

        recommendation = self._get_recommendation(level)

        return RiskAssessment(
            service=service.name,
            score=score,
            level=level,
            factors=factors,
            recommendation=recommendation,
        )

    @staticmethod
    def _get_risk_level(score: int) -> RiskLevel:
        if score >= 75:
            return RiskLevel.CRITICAL

        if score >= 50:
            return RiskLevel.HIGH

        if score >= 25:
            return RiskLevel.MEDIUM

        return RiskLevel.LOW

    @staticmethod
    def _get_recommendation(
        level: RiskLevel,
    ) -> str:
        recommendations = {
            RiskLevel.LOW: (
                "Deployment can proceed using the standard "
                "deployment process."
            ),
            RiskLevel.MEDIUM: (
                "Consider additional integration testing and "
                "enhanced monitoring during deployment."
            ),
            RiskLevel.HIGH: (
                "Use a staged or canary deployment and closely "
                "monitor production metrics."
            ),
            RiskLevel.CRITICAL: (
                "Deployment should require additional review, "
                "staging validation, and a controlled canary rollout."
            ),
        }

        return recommendations[level]