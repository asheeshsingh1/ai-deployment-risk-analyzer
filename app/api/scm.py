from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.analyzer.schemas import ChangeAnalysis
from app.analyzer.service import ChangeAnalyzer
from app.db.database import get_db
from app.risk.schemas import ChangeRequestRiskAssessment
from app.risk.service import ChangeRequestRiskService
from app.scm.factory import get_scm_provider


router = APIRouter(
    prefix="/api/v1/scm",
    tags=["scm"],
)


@router.get(
    "/{provider}/{owner}/{repo}/changes/{change_number}",
    response_model=ChangeAnalysis,
)
def analyze_change(
    provider: str,
    owner: str,
    repo: str,
    change_number: int,
    db: Session = Depends(get_db),
) -> ChangeAnalysis:
    try:
        normalized_provider = provider.lower()

        scm_provider = get_scm_provider(
            normalized_provider
        )

        change_request = (
            scm_provider.get_change_request(
                owner=owner,
                repository=repo,
                change_number=change_number,
            )
        )

        analyzer = ChangeAnalyzer(db)

        return analyzer.analyze(
            repository=f"{owner}/{repo}",
            provider=normalized_provider,
            change_request=change_request,
        )

    except ValueError as exc:
        raise HTTPException(
            status_code=400,
            detail=str(exc),
        ) from exc


@router.get(
    "/{provider}/{owner}/{repo}/changes/{change_number}/risk",
    response_model=ChangeRequestRiskAssessment,
)
def assess_change_risk(
    provider: str,
    owner: str,
    repo: str,
    change_number: int,
    db: Session = Depends(get_db),
) -> ChangeRequestRiskAssessment:
    try:
        normalized_provider = provider.lower()

        scm_provider = get_scm_provider(
            normalized_provider
        )

        change_request = (
            scm_provider.get_change_request(
                owner=owner,
                repository=repo,
                change_number=change_number,
            )
        )

        analyzer = ChangeAnalyzer(db)

        change_analysis = analyzer.analyze(
            repository=f"{owner}/{repo}",
            provider=normalized_provider,
            change_request=change_request,
        )

        risk_service = ChangeRequestRiskService(db)

        return risk_service.assess(
            change_analysis=change_analysis,
            change_request=change_request,
        )

    except ValueError as exc:
        raise HTTPException(
            status_code=400,
            detail=str(exc),
        ) from exc