from app.db.models import Deployment, Incident
from app.history.repository import HistoryRepository
from app.history.schemas import (
    DeploymentIngestionRequest,
    DeploymentIngestionResponse,
    IncidentIngestionRequest,
    IncidentIngestionResponse,
)


class HistoryIngestionService:
    def __init__(
        self,
        repository: HistoryRepository,
    ):
        self.repository = repository

    def ingest_deployment(
        self,
        request: DeploymentIngestionRequest,
    ) -> DeploymentIngestionResponse:
        service = self.repository.get_service(
            request.service_id,
        )

        if service is None:
            raise ValueError(f"Service {request.service_id} does not exist.")

        if service.repository_id != request.repository_id:
            raise ValueError("Service does not belong to the specified repository.")

        existing = self.repository.get_deployment_by_commit(
            repository_id=request.repository_id,
            service_id=request.service_id,
            commit_sha=request.commit_sha,
        )

        if existing is not None:
            return DeploymentIngestionResponse(
                id=existing.id,
                repository_id=existing.repository_id,
                service_id=existing.service_id,
                commit_sha=existing.commit_sha,
                status=existing.status,
                deployed_at=existing.deployed_at,
                created=False,
            )

        deployment = Deployment(
            repository_id=request.repository_id,
            service_id=request.service_id,
            commit_sha=request.commit_sha,
            status=request.status,
            deployed_at=request.deployed_at,
        )

        deployment = self.repository.add_deployment(
            deployment,
        )

        return DeploymentIngestionResponse(
            id=deployment.id,
            repository_id=deployment.repository_id,
            service_id=deployment.service_id,
            commit_sha=deployment.commit_sha,
            status=deployment.status,
            deployed_at=deployment.deployed_at,
            created=True,
        )

    def ingest_incident(
        self,
        request: IncidentIngestionRequest,
    ) -> IncidentIngestionResponse:
        service = self.repository.get_service(
            request.service_id,
        )

        if service is None:
            raise ValueError(f"Service {request.service_id} does not exist.")

        existing = self.repository.get_incident(
            service_id=request.service_id,
            title=request.title,
            started_at=request.started_at,
        )

        if existing is not None:
            return IncidentIngestionResponse(
                id=existing.id,
                service_id=existing.service_id,
                deployment_id=existing.deployment_id,
                title=existing.title,
                description=existing.description,
                severity=existing.severity,
                started_at=existing.started_at,
                resolved_at=existing.resolved_at,
                created=False,
            )

        incident = Incident(
            service_id=request.service_id,
            deployment_id=request.deployment_id,
            title=request.title,
            description=request.description,
            severity=request.severity,
            started_at=request.started_at,
            resolved_at=request.resolved_at,
        )

        incident = self.repository.add_incident(
            incident,
        )

        return IncidentIngestionResponse(
            id=incident.id,
            service_id=incident.service_id,
            deployment_id=incident.deployment_id,
            title=incident.title,
            description=incident.description,
            severity=incident.severity,
            started_at=incident.started_at,
            resolved_at=incident.resolved_at,
            created=True,
        )
