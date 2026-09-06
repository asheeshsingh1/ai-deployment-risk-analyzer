from sqlalchemy import select
from sqlalchemy.orm import Session

from app.analyzer.schemas import ChangeAnalysis
from app.db.models import Service
from app.graph.workflow import build_risk_graph
from app.history.service import (
    HistoricalIntelligenceService,
)
from app.risk.engine import RiskEngine
from app.risk.repository import RiskRepository
from app.risk.schemas import (
    ChangeRequestRiskAssessment,
    RiskLevel,
)
from app.scm.schemas import CodeChangeRequest


class ChangeRequestRiskService:
    def __init__(self, db: Session):
        self.db = db

        self.repository = RiskRepository(db)

        self.historical_service = HistoricalIntelligenceService(
            repository=self.repository,
        )

        self.risk_engine = RiskEngine(
            repository=self.repository,
        )

        self.risk_graph = build_risk_graph()

    def assess(
        self,
        change_analysis: ChangeAnalysis,
        change_request: CodeChangeRequest,
    ) -> ChangeRequestRiskAssessment:
        service_assessments = []

        for service_name in change_analysis.affected_services:
            service = self.db.scalar(
                select(Service).where(
                    Service.name == service_name,
                )
            )

            if service is None:
                continue

            historical_intelligence = self.historical_service.analyze(
                service_id=service.id,
                service_name=service.name,
                days=30,
            )

            assessment = self.risk_engine.assess(
                service_name=service.name,
                service_id=service.id,
                risk_signals=(change_analysis.risk_signals),
                historical_intelligence=(historical_intelligence),
            )

            service_assessments.append(assessment)

        if service_assessments:
            overall_assessment = max(
                service_assessments,
                key=lambda assessment: assessment.score,
            )

            overall_score = overall_assessment.score

            overall_level = overall_assessment.level

            recommendation = overall_assessment.recommendation

        else:
            overall_score = 0
            overall_level = RiskLevel.LOW

            recommendation = (
                "Affected service could not be identified. "
                "Review the change manually before deployment."
            )

        risk_assessment = ChangeRequestRiskAssessment(
            repository=change_analysis.repository,
            change_request_number=change_request.number,
            change_request_title=change_request.title,
            affected_services=(change_analysis.affected_services),
            change_types=(change_analysis.change_types),
            risk_signals=(change_analysis.risk_signals),
            files_changed=(change_analysis.files_changed),
            lines_added=(change_analysis.lines_added),
            lines_deleted=(change_analysis.lines_deleted),
            changed_files=(change_analysis.changed_files),
            service_assessments=(service_assessments),
            overall_score=overall_score,
            overall_level=overall_level,
            recommendation=recommendation,
            ai_explanation="",
            ai_recommendation="",
        )

        graph_result = self.risk_graph.invoke(
            {
                "risk_assessment": risk_assessment,
            }
        )

        return risk_assessment.model_copy(
            update={
                "ai_explanation": (
                    graph_result.get(
                        "explanation",
                        "",
                    )
                ),
                "ai_recommendation": (
                    graph_result.get(
                        "recommendation",
                        "",
                    )
                ),
            }
        )
