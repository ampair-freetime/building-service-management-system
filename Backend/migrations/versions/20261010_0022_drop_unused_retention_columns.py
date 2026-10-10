"""Drop retention columns that no code ever wrote.

lost_items.expires_at, lost_items.archived_at and images.purge_after were added in 0004
for a future retention job that was never built. Status `closed` replaced archiving.
Downgrade re-creates them empty, the same as they always were.
"""
from alembic import op
import sqlalchemy as sa

revision = "20261010_0022"
down_revision = "20261008_0021"
branch_labels = None
depends_on = None


def upgrade():
    op.drop_index("ix_lost_items_expires_at", table_name="lost_items")
    op.drop_column("lost_items", "expires_at")
    op.drop_column("lost_items", "archived_at")
    op.drop_index("ix_images_purge_after", table_name="images")
    op.drop_column("images", "purge_after")


def downgrade():
    op.add_column("images", sa.Column("purge_after", sa.DateTime(timezone=True), nullable=True))
    op.create_index("ix_images_purge_after", "images", ["purge_after"])
    op.add_column("lost_items", sa.Column("archived_at", sa.DateTime(timezone=True), nullable=True))
    op.add_column("lost_items", sa.Column("expires_at", sa.DateTime(timezone=True), nullable=True))
    op.create_index("ix_lost_items_expires_at", "lost_items", ["expires_at"])
