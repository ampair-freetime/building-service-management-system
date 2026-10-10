"""Persist pickup window end; existing appointments remain unchanged."""
from alembic import op
import sqlalchemy as sa
revision = "20261007_0020"
down_revision = "20261006_0019"
branch_labels = None
depends_on = None

def upgrade():
    op.add_column("lost_claims", sa.Column("pickup_end_datetime", sa.DateTime(timezone=True), nullable=True))

def downgrade():
    op.drop_column("lost_claims", "pickup_end_datetime")
