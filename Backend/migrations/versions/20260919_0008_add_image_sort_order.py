"""add image sort order

Revision ID: 20260919_0008
Revises: 8e077443860d
Create Date: 2026-09-19
"""

import sqlalchemy as sa
from alembic import op

revision: str = "20260919_0008"
down_revision: str | None = "8e077443860d"
branch_labels: str | None = None
depends_on: str | None = None


def upgrade() -> None:
    op.add_column("images", sa.Column("sort_order", sa.SmallInteger(), nullable=True))


def downgrade() -> None:
    op.drop_column("images", "sort_order")


