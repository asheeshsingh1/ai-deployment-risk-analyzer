from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, Field
from sqlalchemy import select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.db.database import get_db
from app.db.models import Repository


class RepositoryCreate(BaseModel):
    name: str = Field(min_length=1, max_length=255)
    provider: str = Field(min_length=1, max_length=50)
    owner: str = Field(min_length=1, max_length=255)
    external_name: str = Field(
        min_length=1,
        max_length=255,
    )


class RepositoryResponse(RepositoryCreate):
    id: int


router = APIRouter(
    prefix="/api/v1/repositories",
    tags=["repositories"],
)


SUPPORTED_PROVIDERS = {
    "github",
    "gitlab",
}


@router.post(
    "",
    response_model=RepositoryResponse,
    status_code=201,
)
def create_repository(
    payload: RepositoryCreate,
    db: Session = Depends(get_db),
) -> RepositoryResponse:
    provider = payload.provider.lower()

    if provider not in SUPPORTED_PROVIDERS:
        raise HTTPException(
            status_code=400,
            detail=(
                f"Unsupported provider: {payload.provider}. "
                f"Supported providers: "
                f"{sorted(SUPPORTED_PROVIDERS)}"
            ),
        )

    repository = Repository(
        name=payload.name,
        provider=provider,
        owner=payload.owner,
        external_name=payload.external_name,
    )

    db.add(repository)

    try:
        db.commit()
        db.refresh(repository)

    except IntegrityError as exc:
        db.rollback()

        raise HTTPException(
            status_code=409,
            detail="Repository is already registered.",
        ) from exc

    return RepositoryResponse(
        id=repository.id,
        name=repository.name,
        provider=repository.provider,
        owner=repository.owner,
        external_name=repository.external_name,
    )


@router.get(
    "/{provider}/{owner}/{external_name}",
    response_model=RepositoryResponse,
)
def get_repository(
    provider: str,
    owner: str,
    external_name: str,
    db: Session = Depends(get_db),
) -> RepositoryResponse:
    statement = select(Repository).where(
        Repository.provider == provider.lower(),
        Repository.owner == owner,
        Repository.external_name == external_name,
    )

    repository = db.scalar(statement)

    if repository is None:
        raise HTTPException(
            status_code=404,
            detail="Repository not found.",
        )

    return RepositoryResponse(
        id=repository.id,
        name=repository.name,
        provider=repository.provider,
        owner=repository.owner,
        external_name=repository.external_name,
    )
