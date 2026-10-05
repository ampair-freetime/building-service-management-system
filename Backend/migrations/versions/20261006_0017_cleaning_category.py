"""Persist cleaning categories without changing existing requests."""
import sqlalchemy as sa
from alembic import op

revision = "20261006_0017"
down_revision = "20261006_0016"
branch_labels = None
depends_on = None

def upgrade():
    op.add_column("service_requests", sa.Column("cleaning_category", sa.String(100), nullable=True))

def downgrade():
    op.drop_column("service_requests", "cleaning_category")
