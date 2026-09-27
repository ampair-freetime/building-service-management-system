"""Add single-use staff account invitation records.

Revision ID: 20260928_0010
Revises: fc38f883513e
Create Date: 2026-09-28
"""

import sqlalchemy as sa
from alembic import op

revision: str = "20260928_0010"
down_revision: str | None = "fc38f883513e"
branch_labels: str | None = None
depends_on: str | None = None


def upgrade() -> None:
    op.create_table(
        "staff_invitations",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("staff_id", sa.Uuid(), nullable=False),
        # Only SHA-256 hashes of high-entropy tokens are persisted.
        sa.Column("token_hash", sa.String(length=64), nullable=False),
        sa.Column("expires_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("used_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("invalidated_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column(
            "delivery_status", sa.String(length=20), server_default="pending", nullable=False
        ),
        sa.Column("sent_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column(
            "created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False
        ),
        sa.ForeignKeyConstraint(["staff_id"], ["staff.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_staff_invitations_staff_id", "staff_invitations", ["staff_id"])
    op.create_index(
        "ix_staff_invitations_token_hash", "staff_invitations", ["token_hash"], unique=True
    )
    op.create_index("ix_staff_invitations_expires_at", "staff_invitations", ["expires_at"])


def downgrade() -> None:
    op.drop_index("ix_staff_invitations_expires_at", table_name="staff_invitations")
    op.drop_index("ix_staff_invitations_token_hash", table_name="staff_invitations")
    op.drop_index("ix_staff_invitations_staff_id", table_name="staff_invitations")
    op.drop_table("staff_invitations")
