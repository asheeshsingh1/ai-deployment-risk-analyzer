"""make repositories scm agnostic

Revision ID: 91a7c4e82f10
Revises: 7f8c91d4e2ab
Create Date: 2026-09-06 11:00:00.000000
"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


revision: str = "91a7c4e82f10"
down_revision: Union[str, Sequence[str], None] = "7f8c91d4e2ab"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column(
        "repositories",
        sa.Column(
            "provider",
            sa.String(length=50),
            nullable=False,
            server_default="github",
        ),
    )

    op.alter_column(
        "repositories",
        "github_owner",
        new_column_name="owner",
    )

    op.alter_column(
        "repositories",
        "github_repo",
        new_column_name="external_name",
    )

    op.drop_constraint(
        "uq_repository_github_repo",
        "repositories",
        type_="unique",
    )

    op.create_unique_constraint(
        "uq_repository_provider_owner_name",
        "repositories",
        [
            "provider",
            "owner",
            "external_name",
        ],
    )

    op.alter_column(
        "repositories",
        "provider",
        server_default=None,
    )


def downgrade() -> None:
    op.drop_constraint(
        "uq_repository_provider_owner_name",
        "repositories",
        type_="unique",
    )

    op.create_unique_constraint(
        "uq_repository_github_repo",
        "repositories",
        [
            "owner",
            "external_name",
        ],
    )

    op.alter_column(
        "repositories",
        "external_name",
        new_column_name="github_repo",
    )

    op.alter_column(
        "repositories",
        "owner",
        new_column_name="github_owner",
    )

    op.drop_column(
        "repositories",
        "provider",
    )