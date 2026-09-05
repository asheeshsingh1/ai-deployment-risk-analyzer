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
)


def seed_database() -> None:
    db = SessionLocal()

    try:
        # Make the script idempotent.
        # Running it multiple times should not create duplicate data.
        db.execute(delete(Incident))
        db.execute(delete(Deployment))
        db.execute(delete(Service))
        db.execute(delete(Repository))
        db.commit()

        now = datetime.now(timezone.utc)

        # ---------------------------------------------------------
        # Repository
        # ---------------------------------------------------------

        repository = Repository(
            name="payments-platform",
            github_owner="example-org",
            github_repo="payments-platform",
        )

        db.add(repository)
        db.flush()

        # ---------------------------------------------------------
        # Services
        # ---------------------------------------------------------

        payment_service = Service(
            repository_id=repository.id,
            name="payment-service",
        )

        billing_service = Service(
            repository_id=repository.id,
            name="billing-service",
        )

        user_service = Service(
            repository_id=repository.id,
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

        # ---------------------------------------------------------
        # Deployment history
        # ---------------------------------------------------------

        deployments = [
            Deployment(
                repository_id=repository.id,
                service_id=payment_service.id,
                commit_sha="a1b2c3d4e5f6",
                status=DeploymentStatus.SUCCESS,
                deployed_at=now - timedelta(days=30),
            ),
            Deployment(
                repository_id=repository.id,
                service_id=payment_service.id,
                commit_sha="b2c3d4e5f6a7",
                status=DeploymentStatus.SUCCESS,
                deployed_at=now - timedelta(days=25),
            ),
            Deployment(
                repository_id=repository.id,
                service_id=payment_service.id,
                commit_sha="c3d4e5f6a7b8",
                status=DeploymentStatus.FAILED,
                deployed_at=now - timedelta(days=20),
            ),
            Deployment(
                repository_id=repository.id,
                service_id=payment_service.id,
                commit_sha="d4e5f6a7b8c9",
                status=DeploymentStatus.ROLLED_BACK,
                deployed_at=now - timedelta(days=15),
            ),
            Deployment(
                repository_id=repository.id,
                service_id=payment_service.id,
                commit_sha="e5f6a7b8c9d0",
                status=DeploymentStatus.SUCCESS,
                deployed_at=now - timedelta(days=10),
            ),
            Deployment(
                repository_id=repository.id,
                service_id=payment_service.id,
                commit_sha="f6a7b8c9d0e1",
                status=DeploymentStatus.SUCCESS,
                deployed_at=now - timedelta(days=5),
            ),
            Deployment(
                repository_id=repository.id,
                service_id=billing_service.id,
                commit_sha="111aaa222bbb",
                status=DeploymentStatus.SUCCESS,
                deployed_at=now - timedelta(days=12),
            ),
            Deployment(
                repository_id=repository.id,
                service_id=billing_service.id,
                commit_sha="222bbb333ccc",
                status=DeploymentStatus.SUCCESS,
                deployed_at=now - timedelta(days=6),
            ),
            Deployment(
                repository_id=repository.id,
                service_id=user_service.id,
                commit_sha="333ccc444ddd",
                status=DeploymentStatus.SUCCESS,
                deployed_at=now - timedelta(days=8),
            ),
        ]

        db.add_all(deployments)
        db.flush()

        # ---------------------------------------------------------
        # Incidents
        # ---------------------------------------------------------

        incidents = [
            Incident(
                service_id=payment_service.id,
                deployment_id=deployments[2].id,
                title="Payment API elevated error rate",
                description=(
                    "Payment failures increased after deployment. "
                    "Rollback was required."
                ),
                severity=IncidentSeverity.HIGH,
                started_at=now - timedelta(days=20),
                resolved_at=now - timedelta(days=20, hours=-2),
            ),
            Incident(
                service_id=payment_service.id,
                deployment_id=deployments[3].id,
                title="Payment service latency spike",
                description=(
                    "P99 latency increased significantly after deployment."
                ),
                severity=IncidentSeverity.MEDIUM,
                started_at=now - timedelta(days=15),
                resolved_at=now - timedelta(days=14, hours=-4),
            ),
            Incident(
                service_id=billing_service.id,
                deployment_id=deployments[6].id,
                title="Billing API timeout",
                description=(
                    "Temporary timeout issues following billing deployment."
                ),
                severity=IncidentSeverity.LOW,
                started_at=now - timedelta(days=12),
                resolved_at=now - timedelta(days=12, hours=-1),
            ),
        ]

        db.add_all(incidents)

        db.commit()

        print("Database seeded successfully.")
        print()
        print(f"Repository: {repository.name}")
        print(
            "Services:",
            payment_service.name,
            billing_service.name,
            user_service.name,
        )
        print(f"Deployments: {len(deployments)}")
        print(f"Incidents: {len(incidents)}")

    except Exception:
        db.rollback()
        raise

    finally:
        db.close()


if __name__ == "__main__":
    seed_database()