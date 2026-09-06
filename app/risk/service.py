from sqlalchemy.orm import Session

from app.analyzer.schemas import ChangeAnalysis
from app.graph.workflow import build_risk_graph
from app.risk.engine import RiskEngine
from app.risk.schemas import (
    ChangeRequestRiskAssessment,
    ChangedFile,
    RiskAssessment,
    RiskLevel,
)
from app.scm.schemas import CodeChangeRequest


class PRRiskService:
    def __init__(self, db: Session):
        self.db = db
        self.risk_engine = RiskEngine(db)
        self.graph = build_risk_graph()

    def assess(
        self,
        change_analysis: ChangeAnalysis,
        change_request: CodeChangeRequest,
    ) -> ChangeRequestRiskAssessment:
        service_assessments: list[RiskAssessment] = []

        for service_name in change_analysis.affected_services:
            assessment = self.risk_engine.assess(
                service_name
            )

            service_assessments.append(assessment)

        if service_assessments:
            overall_score = max(
                assessment.score
                for assessment in service_assessments
            )

            overall_level = self._calculate_level(
                overall_score
            )

        else:
            overall_score = self._calculate_unmapped_score(
                change_analysis
            )

            overall_level = self._calculate_level(
                overall_score
            )

        recommendation = self._build_recommendation(
            overall_level=overall_level,
            service_assessments=service_assessments,
            change_analysis=change_analysis,
        )

        deterministic_assessment = (
            ChangeRequestRiskAssessment(
                repository=change_analysis.repository,
                change_request_number=(
                    change_analysis.change_request_number
                ),
                change_request_title=change_request.title,
                affected_services=(
                    change_analysis.affected_services
                ),
                change_types=change_analysis.change_types,
                risk_signals=change_analysis.risk_signals,
                files_changed=change_analysis.files_changed,
                lines_added=change_analysis.lines_added,
                lines_deleted=change_analysis.lines_deleted,
                changed_files=[
                    ChangedFile(
                        filename=file.filename,
                        status=file.status,
                        additions=file.additions,
                        deletions=file.deletions,
                        changes=file.changes,
                        patch=file.patch,
                    )
                    for file in change_request.files
                ],
                service_assessments=service_assessments,
                overall_score=overall_score,
                overall_level=overall_level,
                recommendation=recommendation,
                ai_explanation="",
                ai_recommendation="",
            )
        )

        graph_result = self.graph.invoke(
            {
                "risk_assessment": (
                    deterministic_assessment
                )
            }
        )

        return deterministic_assessment.model_copy(
            update={
                "ai_explanation": graph_result.get(
                    "explanation",
                    "",
                ),
                "ai_recommendation": graph_result.get(
                    "recommendation",
                    "",
                ),
            }
        )

    @staticmethod
    def _calculate_level(score: int) -> RiskLevel:
        if score >= 75:
            return RiskLevel.CRITICAL

        if score >= 50:
            return RiskLevel.HIGH

        if score >= 25:
            return RiskLevel.MEDIUM

        return RiskLevel.LOW

    @staticmethod
    def _calculate_unmapped_score(
        change_analysis: ChangeAnalysis,
    ) -> int:
        score = 0

        if change_analysis.files_changed >= 10:
            score += 20
        elif change_analysis.files_changed >= 5:
            score += 10

        if change_analysis.lines_added >= 500:
            score += 20
        elif change_analysis.lines_added >= 100:
            score += 10

        if "database" in change_analysis.change_types:
            score += 20

        if "infrastructure" in change_analysis.change_types:
            score += 20

        if "api" in change_analysis.change_types:
            score += 10

        return min(score, 100)

    @staticmethod
    def _build_recommendation(
        overall_level: RiskLevel,
        service_assessments: list[RiskAssessment],
        change_analysis: ChangeAnalysis,
    ) -> str:
        if not service_assessments:
            if (
                "database"
                in change_analysis.change_types
                or "infrastructure"
                in change_analysis.change_types
            ):
                return (
                    "Affected service could not be identified. "
                    "Validate service ownership before deployment."
                )

            return (
                "Affected service could not be identified. "
                "Review the change manually before deployment."
            )

        if overall_level == RiskLevel.CRITICAL:
            return (
                "Do not perform a direct production deployment. "
                "Use a staged or canary deployment with "
                "explicit approval and close monitoring."
            )

        if overall_level == RiskLevel.HIGH:
            return (
                "Use a staged or canary deployment and "
                "closely monitor production metrics."
            )

        if overall_level == RiskLevel.MEDIUM:
            return (
                "Consider a staged deployment and monitor "
                "the affected service after release."
            )

        return (
            "Standard deployment is reasonable with normal "
            "production monitoring."
        )