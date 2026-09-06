from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, Field
from sqlalchemy import select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.db.database import get_db
from app.db.models import Repository, Service, ServicePath


class ServiceCreate(BaseModel):
    name: str = Field(min_length=1, max_length=255)
    repository_id: int


class ServiceResponse(BaseModel):
    id: int
    name: str
    repository_id: int


class ServicePathCreate(BaseModel):
    path_prefix: str = Field(min_length=1, max_length=500)


class ServicePathResponse(BaseModel):
    id: int
    service_id: int
    path_prefix: str


router = APIRouter(
    prefix="/api/v1",
    tags=["services"],
)


@router.post(
    "/repositories/{repository_id}/services",
    response_model=ServiceResponse,
    status_code=201,
)
def create_service(
    repository_id: int,
    payload: ServiceCreate,
    db: Session = Depends(get_db),
) -> ServiceResponse:
    if payload.repository_id != repository_id:
        raise HTTPException(
            status_code=400,
            detail="repository_id in body does not match URL.",
        )

    repository = db.get(
        Repository,
        repository_id,
    )

    if repository is None:
        raise HTTPException(
            status_code=404,
            detail="Repository not found.",
        )

    service = Service(
        name=payload.name,
        repository_id=repository_id,
    )

    db.add(service)

    try:
        db.commit()
        db.refresh(service)

    except IntegrityError as exc:
        db.rollback()

        raise HTTPException(
            status_code=409,
            detail="Service is already registered.",
        ) from exc

    return ServiceResponse(
        id=service.id,
        name=service.name,
        repository_id=service.repository_id,
    )


@router.get(
    "/repositories/{repository_id}/services",
    response_model=list[ServiceResponse],
)
def list_services(
    repository_id: int,
    db: Session = Depends(get_db),
) -> list[ServiceResponse]:
    repository = db.get(
        Repository,
        repository_id,
    )

    if repository is None:
        raise HTTPException(
            status_code=404,
            detail="Repository not found.",
        )

    statement = (
        select(Service)
        .where(
            Service.repository_id == repository_id,
        )
        .order_by(Service.name)
    )

    services = list(
        db.scalars(statement).all()
    )

    return [
        ServiceResponse(
            id=service.id,
            name=service.name,
            repository_id=service.repository_id,
        )
        for service in services
    ]


@router.post(
    "/services/{service_id}/paths",
    response_model=ServicePathResponse,
    status_code=201,
)
def create_service_path(
    service_id: int,
    payload: ServicePathCreate,
    db: Session = Depends(get_db),
) -> ServicePathResponse:
    service = db.get(
        Service,
        service_id,
    )

    if service is None:
        raise HTTPException(
            status_code=404,
            detail="Service not found.",
        )


    normalized_path = payload.path_prefix.strip().strip("/")

    if not normalized_path:
        raise HTTPException(
            status_code=400,
            detail="path_prefix cannot be empty.",
        )

    service_path = ServicePath(
        service_id=service_id,
        path_prefix=normalized_path,
    )

    db.add(service_path)

    try:
        db.commit()
        db.refresh(service_path)

    except IntegrityError as exc:
        db.rollback()

        raise HTTPException(
            status_code=409,
            detail="Service path is already registered.",
        ) from exc

    return ServicePathResponse(
        id=service_path.id,
        service_id=service_path.service_id,
        path_prefix=service_path.path_prefix,
    )


@router.get(
    "/services/{service_id}/paths",
    response_model=list[ServicePathResponse],
)
def list_service_paths(
    service_id: int,
    db: Session = Depends(get_db),
) -> list[ServicePathResponse]:

    service = db.get(
        Service,
        service_id,
    )

    if service is None:
        raise HTTPException(
            status_code=404,
            detail="Service not found.",
        )

    statement = (
        select(ServicePath)
        .where(
            ServicePath.service_id == service_id,
        )
        .order_by(ServicePath.path_prefix)
    )

    paths = list(
        db.scalars(statement).all()
    )

    return [
        ServicePathResponse(
            id=service_path.id,
            service_id=service_path.service_id,
            path_prefix=service_path.path_prefix,
        )
        for service_path in paths
    ]