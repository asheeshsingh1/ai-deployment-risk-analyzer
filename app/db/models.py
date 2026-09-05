from datetime import datetime
from enum import Enum

from sqlalchemy import (
    DateTime,
    Enum as SQLEnum,
    ForeignKey,
    Integer,
    String,
    Text,
    UniqueConstraint,
)
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.database import Base


class DeploymentStatus(str, Enum):
    SUCCESS = "success"
    FAILED = "failed"
    ROLLED_BACK = "rolled_back"


class IncidentSeverity(str, Enum):
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"


class Repository(Base):
    __tablename__ = "repositories"

    id: Mapped[int] = mapped_column(
        Integer,
        primary_key=True,
    )

    name: Mapped[str] = mapped_column(
        String(255),
        nullable=False,
    )

    github_owner: Mapped[str] = mapped_column(
        String(255),
        nullable=False,
    )

    github_repo: Mapped[str] = mapped_column(
        String(255),
        nullable=False,
    )

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=datetime.utcnow,
        nullable=False,
    )

    services: Mapped[list["Service"]] = relationship(
        back_populates="repository",
        cascade="all, delete-orphan",
    )

    deployments: Mapped[list["Deployment"]] = relationship(
        back_populates="repository",
        cascade="all, delete-orphan",
    )

    __table_args__ = (
        UniqueConstraint(
            "github_owner",
            "github_repo",
            name="uq_repository_github_repo",
        ),
    )


class Service(Base):
    __tablename__ = "services"

    id: Mapped[int] = mapped_column(
        Integer,
        primary_key=True,
    )

    repository_id: Mapped[int] = mapped_column(
        ForeignKey("repositories.id"),
        nullable=False,
    )

    name: Mapped[str] = mapped_column(
        String(255),
        nullable=False,
    )

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=datetime.utcnow,
        nullable=False,
    )

    repository: Mapped["Repository"] = relationship(
        back_populates="services",
    )

    deployments: Mapped[list["Deployment"]] = relationship(
        back_populates="service",
    )

    incidents: Mapped[list["Incident"]] = relationship(
        back_populates="service",
    )

    __table_args__ = (
        UniqueConstraint(
            "repository_id",
            "name",
            name="uq_service_repository_name",
        ),
    )


class Deployment(Base):
    __tablename__ = "deployments"

    id: Mapped[int] = mapped_column(
        Integer,
        primary_key=True,
    )

    repository_id: Mapped[int] = mapped_column(
        ForeignKey("repositories.id"),
        nullable=False,
    )

    service_id: Mapped[int | None] = mapped_column(
        ForeignKey("services.id"),
        nullable=True,
    )

    commit_sha: Mapped[str] = mapped_column(
        String(64),
        nullable=False,
    )

    status: Mapped[DeploymentStatus] = mapped_column(
        SQLEnum(DeploymentStatus),
        nullable=False,
    )

    deployed_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
    )

    repository: Mapped["Repository"] = relationship(
        back_populates="deployments",
    )

    service: Mapped["Service | None"] = relationship(
        back_populates="deployments",
    )

    incidents: Mapped[list["Incident"]] = relationship(
        back_populates="deployment",
    )


class Incident(Base):
    __tablename__ = "incidents"

    id: Mapped[int] = mapped_column(
        Integer,
        primary_key=True,
    )

    service_id: Mapped[int] = mapped_column(
        ForeignKey("services.id"),
        nullable=False,
    )

    deployment_id: Mapped[int | None] = mapped_column(
        ForeignKey("deployments.id"),
        nullable=True,
    )

    title: Mapped[str] = mapped_column(
        String(500),
        nullable=False,
    )

    description: Mapped[str | None] = mapped_column(
        Text,
        nullable=True,
    )

    severity: Mapped[IncidentSeverity] = mapped_column(
        SQLEnum(IncidentSeverity),
        nullable=False,
    )

    started_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
    )

    resolved_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True),
        nullable=True,
    )

    service: Mapped["Service"] = relationship(
        back_populates="incidents",
    )

    deployment: Mapped["Deployment | None"] = relationship(
        back_populates="incidents",
    )