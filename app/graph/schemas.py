from typing import TypedDict

from app.risk.schemas import ChangeRequestRiskAssessment


class RiskGraphState(TypedDict, total=False):
    risk_assessment: ChangeRequestRiskAssessment
    context: str
    explanation: str
    recommendation: str