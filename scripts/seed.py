from datetime import datetime, timedelta, timezone

from sqlalchemy import delete

from app.db.database import SessionLocal
from app.db.models import (
    Deployment,
    DeploymentStatus,
    Incident,
    IncidentSeverity,
    Repository,
    Service,
    ServicePath,
)


def seed() -> None:
    db = SessionLocal()

    try:
        now = datetime.now(timezone.utc)

        # Reset existing seed data.
        db.execute(delete(Incident))
        db.execute(delete(Deployment))
        db.execute(delete(ServicePath))
        db.execute(delete(Service))
        db.execute(delete(Repository))

        # =========================================================
        # payments-platform
        # =========================================================

        payments_repo = Repository(
            name="payments-platform",
            provider="github",
            owner="example",
            external_name="payments-platform",
        )

        db.add(payments_repo)
        db.flush()

        payment_service = Service(
            repository_id=payments_repo.id,
            name="payment-service",
        )

        billing_service = Service(
            repository_id=payments_repo.id,
            name="billing-service",
        )

        user_service = Service(
            repository_id=payments_repo.id,
            name="user-service",
        )

        db.add_all(
            [
                payment_service,
                billing_service,
                user_service,
            ]
        )

        db.flush()

        db.add_all(
            [
                ServicePath(
                    service_id=payment_service.id,
                    path_prefix="services/payment-service",
                ),
                ServicePath(
                    service_id=billing_service.id,
                    path_prefix="services/billing-service",
                ),
                ServicePath(
                    service_id=user_service.id,
                    path_prefix="services/user-service",
                ),
            ]
        )

        db.flush()

        payment_deployments = [
            Deployment(
                repository_id=payments_repo.id,
                service_id=payment_service.id,
                commit_sha="payment-001",
                status=DeploymentStatus.SUCCESS,
                deployed_at=now - timedelta(days=30),
            ),
            Deployment(
                repository_id=payments_repo.id,
                service_id=payment_service.id,
                commit_sha="payment-002",
                status=DeploymentStatus.FAILED,
                deployed_at=now - timedelta(days=25),
            ),
            Deployment(
                repository_id=payments_repo.id,
                service_id=payment_service.id,
                commit_sha="payment-003",
                status=DeploymentStatus.SUCCESS,
                deployed_at=now - timedelta(days=20),
            ),
            Deployment(
                repository_id=payments_repo.id,
                service_id=payment_service.id,
                commit_sha="payment-004",
                status=DeploymentStatus.ROLLED_BACK,
                deployed_at=now - timedelta(days=15),
            ),
            Deployment(
                repository_id=payments_repo.id,
                service_id=payment_service.id,
                commit_sha="payment-005",
                status=DeploymentStatus.SUCCESS,
                deployed_at=now - timedelta(days=10),
            ),
            Deployment(
                repository_id=payments_repo.id,
                service_id=payment_service.id,
                commit_sha="payment-006",
                status=DeploymentStatus.SUCCESS,
                deployed_at=now - timedelta(days=5),
            ),
            Deployment(
                repository_id=payments_repo.id,
                service_id=billing_service.id,
                commit_sha="billing-001",
                status=DeploymentStatus.SUCCESS,
                deployed_at=now - timedelta(days=20),
            ),
            Deployment(
                repository_id=payments_repo.id,
                service_id=billing_service.id,
                commit_sha="billing-002",
                status=DeploymentStatus.SUCCESS,
                deployed_at=now - timedelta(days=10),
            ),
            Deployment(
                repository_id=payments_repo.id,
                service_id=user_service.id,
                commit_sha="user-001",
                status=DeploymentStatus.SUCCESS,
                deployed_at=now - timedelta(days=7),
            ),
        ]

        db.add_all(payment_deployments)
        db.flush()

        db.add_all(
            [
                Incident(
                    service_id=payment_service.id,
                    deployment_id=payment_deployments[1].id,
                    title="Payment API errors",
                    description=("Elevated payment API failures."),
                    severity=IncidentSeverity.HIGH,
                    started_at=now - timedelta(days=20),
                    resolved_at=(now - timedelta(days=20) + timedelta(hours=2)),
                ),
                Incident(
                    service_id=payment_service.id,
                    deployment_id=payment_deployments[3].id,
                    title="Payment rollback",
                    description=("Deployment required rollback."),
                    severity=IncidentSeverity.MEDIUM,
                    started_at=now - timedelta(days=15),
                    resolved_at=(now - timedelta(days=15) + timedelta(hours=4)),
                ),
                Incident(
                    service_id=billing_service.id,
                    deployment_id=payment_deployments[6].id,
                    title="Billing latency",
                    description=("Temporary billing latency increase."),
                    severity=IncidentSeverity.LOW,
                    started_at=now - timedelta(days=12),
                    resolved_at=(now - timedelta(days=12) + timedelta(hours=1)),
                ),
            ]
        )

        # =========================================================
        # tasker
        # =========================================================

        tasker_repo = Repository(
            name="tasker",
            provider="github",
            owner="asheeshsingh1",
            external_name="tasker",
        )

        db.add(tasker_repo)
        db.flush()

        tasker_service = Service(
            repository_id=tasker_repo.id,
            name="tasker-service",
        )

        db.add(tasker_service)
        db.flush()

        # Explicit service ownership.
        db.add_all(
            [
                ServicePath(
                    service_id=tasker_service.id,
                    path_prefix="api",
                ),
                ServicePath(
                    service_id=tasker_service.id,
                    path_prefix="app",
                ),
            ]
        )

        db.flush()

        # ---------------------------------------------------------
        # tasker deployment history
        # ---------------------------------------------------------

        tasker_deployments = [
            Deployment(
                repository_id=tasker_repo.id,
                service_id=tasker_service.id,
                commit_sha="tasker-001",
                status=DeploymentStatus.SUCCESS,
                deployed_at=now - timedelta(days=30),
            ),
            Deployment(
                repository_id=tasker_repo.id,
                service_id=tasker_service.id,
                commit_sha="tasker-002",
                status=DeploymentStatus.SUCCESS,
                deployed_at=now - timedelta(days=25),
            ),
            Deployment(
                repository_id=tasker_repo.id,
                service_id=tasker_service.id,
                commit_sha="tasker-003",
                status=DeploymentStatus.FAILED,
                deployed_at=now - timedelta(days=20),
            ),
            Deployment(
                repository_id=tasker_repo.id,
                service_id=tasker_service.id,
                commit_sha="tasker-004",
                status=DeploymentStatus.ROLLED_BACK,
                deployed_at=now - timedelta(days=15),
            ),
            Deployment(
                repository_id=tasker_repo.id,
                service_id=tasker_service.id,
                commit_sha="tasker-005",
                status=DeploymentStatus.SUCCESS,
                deployed_at=now - timedelta(days=10),
            ),
            Deployment(
                repository_id=tasker_repo.id,
                service_id=tasker_service.id,
                commit_sha="tasker-006",
                status=DeploymentStatus.SUCCESS,
                deployed_at=now - timedelta(days=5),
            ),
        ]

        db.add_all(tasker_deployments)
        db.flush()

        # ---------------------------------------------------------
        # tasker incidents
        # ---------------------------------------------------------

        db.add_all(
            [
                Incident(
                    service_id=tasker_service.id,
                    deployment_id=tasker_deployments[2].id,
                    title="Recurring task failures",
                    description=(
                        "Scheduled recurring tasks failed " "after deployment."
                    ),
                    severity=IncidentSeverity.HIGH,
                    started_at=now - timedelta(days=20),
                    resolved_at=(now - timedelta(days=20) + timedelta(hours=3)),
                ),
                Incident(
                    service_id=tasker_service.id,
                    deployment_id=tasker_deployments[3].id,
                    title="Worker rollback",
                    description=(
                        "Deployment was rolled back after "
                        "elevated task processing errors."
                    ),
                    severity=IncidentSeverity.MEDIUM,
                    started_at=now - timedelta(days=15),
                    resolved_at=(now - timedelta(days=15) + timedelta(hours=2)),
                ),
            ]
        )

        db.commit()

        print("Seed completed successfully.")

    except Exception:
        db.rollback()
        raise

    finally:
        db.close()


if __name__ == "__main__":
    seed()
