"""add received request status

Revision ID: ba8f87912a23
Revises: 8e077443860d
Create Date: 2026-09-19 19:06:39.111116
"""
from collections.abc import Sequence

from alembic import op


revision: str = 'ba8f87912a23'
down_revision: str | None = '8e077443860d'
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.execute(
        "ALTER TYPE request_status ADD VALUE IF NOT EXISTS 'received'"
    )


def downgrade() -> None:
    pass
