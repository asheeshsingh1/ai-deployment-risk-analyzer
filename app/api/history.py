from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.db.database import get_db
from app.history.ingestion import HistoryIngestionService
from app.history.repository import HistoryRepository
from app.history.schemas import (
    DeploymentIngestionRequest,
    DeploymentIngestionResponse,
    IncidentIngestionRequest,
    IncidentIngestionResponse,
)

router = APIRouter(
    prefix="/api/v1/history",
    tags=["history"],
)


@router.post(
    "/deployments",
    response_model=DeploymentIngestionResponse,
    status_code=201,
)
def ingest_deployment(
    request: DeploymentIngestionRequest,
    db: Session = Depends(get_db),
) -> DeploymentIngestionResponse:
    service = HistoryIngestionService(
        repository=HistoryRepository(db),
    )

    try:
        response = service.ingest_deployment(request)

        if not response.created:
            return response

        return response

    except ValueError as exc:
        raise HTTPException(
            status_code=400,
            detail=str(exc),
        ) from exc


@router.post(
    "/incidents",
    response_model=IncidentIngestionResponse,
    status_code=201,
)
def ingest_incident(
    request: IncidentIngestionRequest,
    db: Session = Depends(get_db),
) -> IncidentIngestionResponse:
    service = HistoryIngestionService(
        repository=HistoryRepository(db),
    )

    try:
        response = service.ingest_incident(request)

        if not response.created:
            return response

        return response

    except ValueError as exc:
        raise HTTPException(
            status_code=400,
            detail=str(exc),
        ) from exc
