"""Add additional_info_required status to claim_status enum.

Revision ID: 20260912_0006
Revises: 20260909_0005
Create Date: 2026-09-12
"""

from collections.abc import Sequence

from alembic import op


revision: str = "20260912_0006"
down_revision: str | None = "20260909_0005"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.execute(
        "ALTER TYPE claim_status ADD VALUE IF NOT EXISTS 'additional_info_required'"
    )


def downgrade() -> None:
    # PostgreSQL ไม่รองรับการลบ enum value โดยตรงแบบง่าย ๆ
    # จึงไม่ทำ destructive downgrade สำหรับ migration นี้
    pass
