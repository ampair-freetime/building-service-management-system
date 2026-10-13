"""Ignore spaces in location uniqueness without merging existing records."""
import sqlalchemy as sa
from alembic import op

revision = "20261013_0024"
down_revision = "20261012_0023"
branch_labels = None
depends_on = None
INDEX_NAME = "uq_locations_floor_area"


def upgrade() -> None:
    duplicates = op.get_bind().execute(sa.text("""
        SELECT lower(coalesce(floor, '')) AS floor_key,
               lower(replace(area, ' ', '')) AS area_key, count(*) AS total
        FROM locations
        GROUP BY lower(coalesce(floor, '')), lower(replace(area, ' ', ''))
        HAVING count(*) > 1
    """)).all()
    if duplicates:
        raise RuntimeError("Duplicate locations ignoring spaces; resolve them first: "
                           + str(duplicates))
    op.drop_index(INDEX_NAME, table_name="locations")
    op.create_index(INDEX_NAME, "locations", [
        sa.text("lower(coalesce(floor, ''))"),
        sa.text("lower(replace(area, ' ', ''))"),
    ], unique=True)


def downgrade() -> None:
    op.drop_index(INDEX_NAME, table_name="locations")
    op.create_index(INDEX_NAME, "locations", [
        sa.text("lower(coalesce(floor, ''))"), sa.text("lower(area)"),
    ], unique=True)
