"""Allow locations to exist before their QR code is generated.

Revision ID: 20260923_0010
Revises: fc38f883513e
Create Date: 2026-09-23
"""

import secrets

import sqlalchemy as sa
from alembic import op

revision: str = "20260923_0010"
down_revision: str | None = "fc38f883513e"
branch_labels: str | None = None
depends_on: str | None = None


def upgrade() -> None:
    with op.batch_alter_table("locations") as batch:
        batch.alter_column("qr_token", existing_type=sa.String(length=255), nullable=True)


def downgrade() -> None:
    connection = op.get_bind()
    locations = sa.table(
        "locations",
        sa.column("id", sa.Integer),
        sa.column("qr_token", sa.String(length=255)),
    )
    missing_ids = (
        connection.execute(sa.select(locations.c.id).where(locations.c.qr_token.is_(None)))
        .scalars()
        .all()
    )
    for location_id in missing_ids:
        connection.execute(
            sa.update(locations)
            .where(locations.c.id == location_id)
            .values(qr_token=secrets.token_urlsafe(24))
        )
    with op.batch_alter_table("locations") as batch:
        batch.alter_column("qr_token", existing_type=sa.String(length=255), nullable=False)
