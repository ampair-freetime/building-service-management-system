"""add pickup appointment to lost claims

Revision ID: 22ee51a25eb0
Revises: dbed223972ff
Create Date: 2026-09-18 08:41:14.004847
"""

from collections.abc import Sequence

from alembic import op
import sqlalchemy as sa


revision: str = "22ee51a25eb0"
down_revision: str | None = "dbed223972ff"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.execute(
        "ALTER TYPE claim_status ADD VALUE IF NOT EXISTS 'scheduled'"
    )

    op.add_column(
        "lost_claims",
        sa.Column(
            "pickup_datetime",
            sa.DateTime(timezone=True),
            nullable=True,
        ),
    )


def downgrade() -> None:
    op.drop_column(
        "lost_claims",
        "pickup_datetime",
    )

    # PostgreSQL ลบ enum value ออกตรง ๆ ได้ยาก
    # จึงไม่ลบค่า scheduled ใน downgrade