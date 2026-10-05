"""Add self-service password reset links and staff.password_changed_at.

Revision ID: 20261006_0016
Revises: 20260928_0015
Create Date: 2026-10-06
"""

import sqlalchemy as sa
from alembic import op

revision: str = "20261006_0016"
down_revision: str | None = "20260928_0015"
branch_labels: str | None = None
depends_on: str | None = None


def upgrade() -> None:
    op.add_column(
        "staff", sa.Column("password_changed_at", sa.DateTime(timezone=True), nullable=True)
    )
    # Backfill: accounts activated through an invitation changed their password when
    # the invitation was used. Accounts that predate invitations (e.g. the seeded
    # admin) have no invitation rows and already hold a usable password. Accounts
    # with only unused invitations stay NULL, meaning "not activated yet".
    op.execute(
        """
        UPDATE staff SET password_changed_at = (
            SELECT MAX(staff_invitations.used_at) FROM staff_invitations
            WHERE staff_invitations.staff_id = staff.id
        )
        WHERE EXISTS (
            SELECT 1 FROM staff_invitations
            WHERE staff_invitations.staff_id = staff.id
              AND staff_invitations.used_at IS NOT NULL
        )
        """
    )
    op.execute(
        """
        UPDATE staff SET password_changed_at = created_at
        WHERE password_changed_at IS NULL
          AND NOT EXISTS (
            SELECT 1 FROM staff_invitations WHERE staff_invitations.staff_id = staff.id
          )
        """
    )

    op.create_table(
        "staff_password_resets",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("staff_id", sa.Uuid(), nullable=False),
        # Only SHA-256 hashes of high-entropy tokens are persisted.
        sa.Column("token_hash", sa.String(length=64), nullable=False),
        sa.Column("recipient_email", sa.String(length=255), nullable=False),
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
    op.create_index("ix_staff_password_resets_staff_id", "staff_password_resets", ["staff_id"])
    op.create_index(
        "ix_staff_password_resets_token_hash",
        "staff_password_resets",
        ["token_hash"],
        unique=True,
    )
    op.create_index(
        "ix_staff_password_resets_expires_at", "staff_password_resets", ["expires_at"]
    )


def downgrade() -> None:
    op.drop_index("ix_staff_password_resets_expires_at", table_name="staff_password_resets")
    op.drop_index("ix_staff_password_resets_token_hash", table_name="staff_password_resets")
    op.drop_index("ix_staff_password_resets_staff_id", table_name="staff_password_resets")
    op.drop_table("staff_password_resets")
    with op.batch_alter_table("staff") as batch:
        batch.drop_column("password_changed_at")
