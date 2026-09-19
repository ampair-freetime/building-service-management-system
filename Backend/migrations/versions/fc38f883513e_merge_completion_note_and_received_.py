"""merge completion note and received status branches

Revision ID: fc38f883513e
Revises: 390cfbe1de1a, ba8f87912a23
Create Date: 2026-09-20 00:39:34.804698
"""
from collections.abc import Sequence

from alembic import op
import sqlalchemy as sa


revision: str = 'fc38f883513e'
down_revision: str | None = ('390cfbe1de1a', 'ba8f87912a23')
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    pass


def downgrade() -> None:
    pass
