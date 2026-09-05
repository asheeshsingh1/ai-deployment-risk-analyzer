"""add service paths

Revision ID: 7f8c91d4e2ab
Revises: 3322326f0194
Create Date: 2026-09-05 21:45:00.000000
"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


revision: str = "7f8c91d4e2ab"
down_revision: Union[str, Sequence[str], None] = "3322326f0194"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "service_paths",
        sa.Column(
            "id",
            sa.Integer(),
            nullable=False,
        ),
        sa.Column(
            "service_id",
            sa.Integer(),
            nullable=False,
        ),
        sa.Column(
            "path_prefix",
            sa.String(length=500),
            nullable=False,
        ),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            nullable=False,
        ),
        sa.ForeignKeyConstraint(
            ["service_id"],
            ["services.id"],
        ),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint(
            "service_id",
            "path_prefix",
            name="uq_service_path",
        ),
    )


def downgrade() -> None:
    op.drop_table("service_paths")