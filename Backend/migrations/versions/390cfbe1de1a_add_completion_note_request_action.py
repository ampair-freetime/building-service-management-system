"""add completion note request action

Revision ID: 390cfbe1de1a
Revises: ba8f87912a23
Create Date: 2026-09-19
"""

from collections.abc import Sequence

from alembic import op


revision: str = "390cfbe1de1a"
down_revision: str | None = "20260919_0009"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.execute(
        "ALTER TYPE request_action "
        "ADD VALUE IF NOT EXISTS 'completion_note_added'"
    )


def downgrade() -> None:
    pass
