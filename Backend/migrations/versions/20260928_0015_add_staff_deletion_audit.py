"""Add soft-deletion status and staff deletion audit log.

Revision ID: 20260928_0015
Revises: 20260928_0014
Create Date: 2026-09-28
"""

import sqlalchemy as sa
from alembic import op

revision: str = "20260928_0015"
down_revision: str | None = "20260928_0014"
branch_labels: str | None = None
depends_on: str | None = None


def upgrade() -> None:
    op.execute("ALTER TYPE account_status ADD VALUE IF NOT EXISTS 'deleted'")
    op.create_table(
        "staff_deletion_audit",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("deleted_staff_id", sa.Uuid(), nullable=False),
        sa.Column("deleted_email", sa.String(length=255), nullable=False),
        sa.Column("deleted_full_name", sa.String(length=150), nullable=False),
        sa.Column("deleted_role", sa.String(length=30), nullable=False),
        sa.Column("deleted_by_staff_id", sa.Uuid(), nullable=False),
        sa.Column(
            "created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False
        ),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_staff_deletion_audit_deleted_staff_id", "staff_deletion_audit", ["deleted_staff_id"])
    op.create_index("ix_staff_deletion_audit_deleted_by_staff_id", "staff_deletion_audit", ["deleted_by_staff_id"])


def downgrade() -> None:
    op.drop_index("ix_staff_deletion_audit_deleted_by_staff_id", table_name="staff_deletion_audit")
    op.drop_index("ix_staff_deletion_audit_deleted_staff_id", table_name="staff_deletion_audit")
    op.drop_table("staff_deletion_audit")
    # PostgreSQL enum values are deliberately retained: removing one is unsafe when
    # an upgraded database may already contain a soft-deleted account.
