from sqlalchemy import select
from sqlalchemy.orm import Session

from app.db.models import Deployment, Incident, Service


class HistoryRepository:
    def __init__(self, db: Session):
        self.db = db

    def get_service(self, service_id: int) -> Service | None:
        statement = select(Service).where(
            Service.id == service_id,
        )
        return self.db.scalar(statement)

    def get_deployment_by_commit(
        self,
        repository_id: int,
        service_id: int,
        commit_sha: str,
    ) -> Deployment | None:
        statement = select(Deployment).where(
            Deployment.repository_id == repository_id,
            Deployment.service_id == service_id,
            Deployment.commit_sha == commit_sha,
        )
        return self.db.scalar(statement)

    def get_incident(
        self,
        service_id: int,
        title: str,
        started_at,
    ) -> Incident | None:
        statement = select(Incident).where(
            Incident.service_id == service_id,
            Incident.title == title,
            Incident.started_at == started_at,
        )
        return self.db.scalar(statement)

    def add_deployment(
        self,
        deployment: Deployment,
    ) -> Deployment:
        self.db.add(deployment)
        self.db.commit()
        self.db.refresh(deployment)
        return deployment

    def add_incident(
        self,
        incident: Incident,
    ) -> Incident:
        self.db.add(incident)
        self.db.commit()
        self.db.refresh(incident)
        return incident
