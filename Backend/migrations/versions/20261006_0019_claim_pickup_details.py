"""Persist claim pickup location and instructions."""
from alembic import op
import sqlalchemy as sa
revision = "20261006_0019"
down_revision = "20261006_0018"
branch_labels = None
depends_on = None

def upgrade():
    op.add_column("lost_claims", sa.Column("pickup_location", sa.String(255), nullable=True))
    op.add_column("lost_claims", sa.Column("pickup_note", sa.Text(), nullable=True))

def downgrade():
    op.drop_column("lost_claims", "pickup_note")
    op.drop_column("lost_claims", "pickup_location")
