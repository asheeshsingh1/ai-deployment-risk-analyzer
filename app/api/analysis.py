from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, Field
from sqlalchemy.orm import Session

from app.analyzer.service import ChangeAnalyzer
from app.db.database import get_db
from app.risk.schemas import ChangeRequestRiskAssessment
from app.risk.service import ChangeRequestRiskService
from app.scm.exceptions import (
    SCMAuthenticationError,
    SCMNotFoundError,
    SCMProviderError,
    SCMRateLimitError,
)
from app.scm.factory import get_scm_provider
from app.scm.url_parser import (
    ChangeRequestUrlError,
    ChangeRequestUrlParser,
)

router = APIRouter(
    prefix="/api/v1/analysis",
    tags=["analysis"],
)


class AnalysisRequest(BaseModel):
    change_request_url: str = Field(
        min_length=1,
        description=("GitHub Pull Request or GitLab Merge Request URL."),
    )


def _raise_scm_http_error(
    exc: SCMProviderError,
) -> None:
    if isinstance(exc, SCMAuthenticationError):
        raise HTTPException(
            status_code=502,
            detail={
                "error": "scm_authentication_failed",
                "provider": exc.provider,
                "message": exc.message,
            },
        ) from exc

    if isinstance(exc, SCMNotFoundError):
        raise HTTPException(
            status_code=404,
            detail={
                "error": "scm_resource_not_found",
                "provider": exc.provider,
                "message": exc.message,
            },
        ) from exc

    if isinstance(exc, SCMRateLimitError):
        raise HTTPException(
            status_code=429,
            detail={
                "error": "scm_rate_limit_exceeded",
                "provider": exc.provider,
                "message": exc.message,
            },
        ) from exc

    raise HTTPException(
        status_code=502,
        detail={
            "error": "scm_provider_error",
            "provider": exc.provider,
            "message": exc.message,
        },
    ) from exc


@router.post(
    "",
    response_model=ChangeRequestRiskAssessment,
)
def analyze_change(
    request: AnalysisRequest,
    db: Session = Depends(get_db),
) -> ChangeRequestRiskAssessment:
    try:
        parsed_request = ChangeRequestUrlParser.parse(
            request.change_request_url,
        )

        scm_provider = get_scm_provider(
            parsed_request.provider,
        )

        change_request = scm_provider.get_change_request(
            owner=parsed_request.owner,
            repository=parsed_request.repository,
            change_number=parsed_request.change_number,
        )

        analyzer = ChangeAnalyzer(db)

        change_analysis = analyzer.analyze(
            repository=(f"{parsed_request.owner}/" f"{parsed_request.repository}"),
            provider=parsed_request.provider,
            change_request=change_request,
        )

        risk_service = ChangeRequestRiskService(db)

        result = risk_service.assess(
            change_analysis=change_analysis,
            change_request=change_request,
        )

        db.commit()

        return result

    except ChangeRequestUrlError as exc:
        db.rollback()

        raise HTTPException(
            status_code=400,
            detail={
                "error": "invalid_change_request_url",
                "message": str(exc),
            },
        ) from exc

    except SCMProviderError as exc:
        db.rollback()
        _raise_scm_http_error(exc)

    except ValueError as exc:
        db.rollback()

        raise HTTPException(
            status_code=400,
            detail=str(exc),
        ) from exc

    except Exception:
        db.rollback()
        raise
