"""add return status history

Revision ID: 64e6b46fc548
Revises: 5a266dcc5282
Create Date: 2026-09-15 08:11:23.645116
"""

from collections.abc import Sequence

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

revision: str = "64e6b46fc548"
down_revision: str | None = "5a266dcc5282"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    return_status_enum = postgresql.ENUM(
        "pending",
        "ready_for_pickup",
        "returned",
        name="return_status",
        create_type=False,
    )

    op.create_table(
        "lost_claim_return_status_history",
        sa.Column("id", sa.Integer(), primary_key=True, autoincrement=True),
        sa.Column("claim_id", sa.Uuid(), nullable=False),
        sa.Column("staff_id", sa.Uuid(), nullable=True),
        sa.Column(
            "old_status",
            return_status_enum,
            nullable=True,
        ),
        sa.Column(
            "new_status",
            return_status_enum,
            nullable=False,
        ),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.func.now(),
            nullable=False,
        ),
        sa.ForeignKeyConstraint(
            ["claim_id"],
            ["lost_claims.id"],
        ),
        sa.ForeignKeyConstraint(
            ["staff_id"],
            ["staff.id"],
        ),
    )

    op.create_index(
        "ix_lost_claim_return_status_history_claim_id",
        "lost_claim_return_status_history",
        ["claim_id"],
    )


def downgrade() -> None:
    op.drop_index(
        "ix_lost_claim_return_status_history_claim_id",
        table_name="lost_claim_return_status_history",
    )

    op.drop_table("lost_claim_return_status_history")
