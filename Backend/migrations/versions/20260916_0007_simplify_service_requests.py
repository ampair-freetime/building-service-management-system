"""Store request type directly and require registered service locations.

Revision ID: 20260916_0007
Revises: 20260912_0006

Before upgrading, assign a real registered location to every existing request.
Legacy location details are appended to description before their column is removed.
Category names are intentionally removed; restore a backup to recover them.
"""

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

revision = "20260916_0007"
down_revision = "20260912_0006"
branch_labels = None
depends_on = None


def upgrade() -> None:
    # Prevent writes between validation and the data/structure migration.
    op.execute("LOCK TABLE service_requests, service_categories IN ACCESS EXCLUSIVE MODE")
    op.execute("""
        DO $$
        BEGIN
            IF EXISTS (SELECT 1 FROM service_requests WHERE location_id IS NULL) THEN
                RAISE EXCEPTION 'Assign registered location_id values to all service_requests before upgrading';
            END IF;
            IF EXISTS (
                SELECT 1 FROM service_requests AS r
                LEFT JOIN service_categories AS c ON c.id = r.category_id
                WHERE c.request_type IS NULL
            ) THEN
                RAISE EXCEPTION 'Every service request must have a category with a request_type before upgrading';
            END IF;
        END $$;
    """)
    request_type = postgresql.ENUM("repair", "cleaning", name="request_type", create_type=False)
    op.add_column("service_requests", sa.Column("request_type", request_type, nullable=True))
    op.execute("""
        UPDATE service_requests AS r
        SET request_type = c.request_type
        FROM service_categories AS c
        WHERE r.category_id = c.id
    """)
    op.execute("""
        UPDATE service_requests
        SET description = concat_ws(
            E'\n', NULLIF(description, ''),
            'รายละเอียดสถานที่เดิม: ' || location_detail
        )
        WHERE location_detail IS NOT NULL AND btrim(location_detail) <> ''
    """)
    op.alter_column("service_requests", "request_type", existing_type=request_type, nullable=False)
    op.alter_column("service_requests", "location_id", existing_type=sa.Integer(), nullable=False)
    op.drop_constraint("service_requests_category_id_fkey", "service_requests", type_="foreignkey")
    op.drop_column("service_requests", "category_id")
    op.drop_column("service_requests", "location_detail")
    op.drop_table("service_categories")


def downgrade() -> None:
    raise RuntimeError(
        "This migration removes category data and merges location details into description. "
        "Restore a pre-upgrade backup to recover the original schema and data."
    )
