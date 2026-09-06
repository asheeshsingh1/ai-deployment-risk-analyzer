from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.analyzer.schemas import ChangeAnalysis
from app.analyzer.service import ChangeAnalyzer
from app.config import get_settings
from app.db.database import get_db
from app.scm.github.client import GitHubClient
from app.risk.schemas import AIRiskAssessment
from app.risk.service import ChangeRequestRiskService


router = APIRouter(
    prefix="/api/v1/github",
    tags=["github"],
)


def _get_github_client() -> GitHubClient:
    settings = get_settings()

    return GitHubClient(
        token=settings.github_token,
    )


@router.get(
    "/{owner}/{repo}/pulls/{pull_number}",
    response_model=ChangeAnalysis,
)
def analyze_pull_request(
    owner: str,
    repo: str,
    pull_number: int,
    db: Session = Depends(get_db),
) -> ChangeAnalysis:
    github_client = _get_github_client()

    pull_request = github_client.get_pull_request(
        owner=owner,
        repo=repo,
        pull_number=pull_number,
    )

    analyzer = ChangeAnalyzer(db)

    return analyzer.analyze(
        repository=f"{owner}/{repo}",
        pull_request=pull_request,
    )


@router.get(
    "/{owner}/{repo}/pulls/{pull_number}/risk",
    response_model=AIRiskAssessment,
)
def assess_pull_request_risk(
    owner: str,
    repo: str,
    pull_number: int,
    db: Session = Depends(get_db),
) -> AIRiskAssessment:
    github_client = _get_github_client()

    pull_request = github_client.get_pull_request(
        owner=owner,
        repo=repo,
        pull_number=pull_number,
    )

    analyzer = ChangeAnalyzer(db)

    change_analysis = analyzer.analyze(
        repository=f"{owner}/{repo}",
        pull_request=pull_request,
    )

    risk_service = ChangeRequestRiskService(db)

    return risk_service.assess(
        change_analysis=change_analysis,
        pull_request=pull_request,
    )
