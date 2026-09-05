from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.db.database import get_db
from app.risk.engine import RiskEngine
from app.risk.schemas import RiskAssessment


router = APIRouter(
    prefix="/api/v1/risk",
    tags=["risk"],
)


@router.get(
    "/{service_name}",
    response_model=RiskAssessment,
)
def assess_service_risk(
    service_name: str,
    db: Session = Depends(get_db),
) -> RiskAssessment:
    engine = RiskEngine(db)

    try:
        return engine.assess(service_name)

    except ValueError as exc:
        raise HTTPException(
            status_code=404,
            detail=str(exc),
        ) from exc