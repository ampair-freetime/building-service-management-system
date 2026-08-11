"""เพิ่ม schema หลักของระบบ Building Service Management.

Revision ID: 20260812_0003
Revises: 20260807_0002
Create Date: 2026-08-12
"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

revision: str = "20260812_0003"
down_revision: str | None = "20260807_0002"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def pg_enum(name: str, *values: str) -> postgresql.ENUM:
    """สร้างตัวแทน PostgreSQL enum โดยไม่สั่ง CREATE TYPE ซ้ำตอนสร้างตาราง."""
    return postgresql.ENUM(*values, name=name, create_type=False)


account_status = pg_enum("account_status", "active", "suspended")
request_type = pg_enum("request_type", "repair", "cleaning")
request_status = pg_enum(
    "request_status", "waiting", "assigned", "in_progress", "completed", "cancelled"
)
priority_level = pg_enum("priority_level", "normal", "urgent")
image_type = pg_enum("image_type", "before", "during", "after")
lost_type = pg_enum("lost_type", "lost", "found")
lost_status = pg_enum("lost_status", "pending", "approved", "claimed", "closed", "rejected")
claim_status = pg_enum("claim_status", "pending", "approved", "rejected", "completed")
request_action = pg_enum(
    "request_action",
    "created",
    "assigned",
    "accepted",
    "status_changed",
    "returned",
    "reassigned",
    "completed",
    "cancelled",
)

new_enums = (
    account_status,
    request_type,
    request_status,
    priority_level,
    image_type,
    lost_type,
    lost_status,
    claim_status,
    request_action,
)


def uuid_column(name: str = "id") -> sa.Column:
    return sa.Column(
        name,
        sa.Uuid(),
        server_default=sa.text("gen_random_uuid()"),
        nullable=False,
    )


def timestamp_column(name: str) -> sa.Column:
    return sa.Column(
        name,
        sa.DateTime(timezone=True),
        server_default=sa.func.now(),
        nullable=False,
    )


def upgrade_staff() -> None:
    """เปลี่ยน staff_accounts เดิมเป็น staff โดยรักษาข้อมูลทุกบัญชี."""
    bind = op.get_bind()
    account_status.create(bind, checkfirst=True)
    op.execute("ALTER TYPE staff_role RENAME VALUE 'coordinator' TO 'clerk'")

    op.rename_table("staff_accounts", "staff")
    op.alter_column("staff", "employee_code", new_column_name="staff_code")
    op.execute("ALTER INDEX ix_staff_accounts_employee_code RENAME TO ix_staff_staff_code")
    op.execute("ALTER INDEX ix_staff_accounts_email RENAME TO ix_staff_email")
    op.execute("ALTER INDEX ix_staff_accounts_role RENAME TO ix_staff_role")

    op.alter_column(
        "staff", "staff_code", existing_type=sa.String(length=32), type_=sa.String(length=30)
    )
    op.alter_column(
        "staff", "email", existing_type=sa.String(length=320), type_=sa.String(length=255)
    )
    op.alter_column(
        "staff", "full_name", existing_type=sa.String(length=200), type_=sa.String(length=150)
    )
    op.add_column(
        "staff",
        sa.Column(
            "status",
            account_status,
            server_default=sa.text("'active'::account_status"),
            nullable=False,
        ),
    )
    op.execute("UPDATE staff SET status = 'suspended' WHERE is_active = false")
    op.add_column("staff", sa.Column("last_login_at", sa.DateTime(timezone=True), nullable=True))
    op.drop_column("staff", "is_active")


def upgrade() -> None:
    """ปรับ staff และสร้างตารางบริการทั้งหมด."""
    upgrade_staff()
    bind = op.get_bind()
    for enum_type in new_enums[1:]:
        enum_type.create(bind, checkfirst=True)

    op.create_table(
        "locations",
        sa.Column("id", sa.Integer(), sa.Identity(), nullable=False),
        sa.Column("building", sa.String(length=100), nullable=False),
        sa.Column("floor", sa.String(length=30), nullable=True),
        sa.Column("room", sa.String(length=100), nullable=True),
        sa.Column("area_type", sa.String(length=50), nullable=True),
        sa.Column("qr_token", sa.String(length=255), nullable=False),
        sa.Column("is_active", sa.Boolean(), server_default=sa.true(), nullable=False),
        timestamp_column("created_at"),
        timestamp_column("updated_at"),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("qr_token"),
    )
    op.create_table(
        "service_categories",
        sa.Column("id", sa.Integer(), sa.Identity(), nullable=False),
        sa.Column("request_type", request_type, nullable=False),
        sa.Column("category_name", sa.String(length=150), nullable=False),
        sa.Column("is_active", sa.Boolean(), server_default=sa.true(), nullable=False),
        timestamp_column("created_at"),
        timestamp_column("updated_at"),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint(
            "request_type", "category_name", name="uq_service_category_type_name"
        ),
    )
    service_categories = sa.table(
        "service_categories",
        sa.column("request_type", request_type),
        sa.column("category_name", sa.String(length=150)),
        sa.column("is_active", sa.Boolean()),
    )
    op.bulk_insert(
        service_categories,
        [
            {"request_type": "repair", "category_name": "ไฟฟ้า", "is_active": True},
            {"request_type": "repair", "category_name": "ประปา", "is_active": True},
            {"request_type": "repair", "category_name": "เครื่องปรับอากาศ", "is_active": True},
            {"request_type": "repair", "category_name": "อุปกรณ์ห้องเรียน", "is_active": True},
            {"request_type": "cleaning", "category_name": "ทำความสะอาดทั่วไป", "is_active": True},
            {"request_type": "cleaning", "category_name": "คราบหกเลอะ", "is_active": True},
            {"request_type": "cleaning", "category_name": "ขยะสะสม", "is_active": True},
            {"request_type": "cleaning", "category_name": "เหตุเร่งด่วน", "is_active": True},
        ],
    )
    op.create_table(
        "service_requests",
        uuid_column(),
        sa.Column("request_code", sa.String(length=30), nullable=False),
        sa.Column("category_id", sa.Integer(), nullable=False),
        sa.Column("location_id", sa.Integer(), nullable=True),
        sa.Column("title", sa.String(length=200), nullable=False),
        sa.Column("description", sa.Text(), nullable=False),
        sa.Column("location_detail", sa.String(length=255), nullable=True),
        sa.Column(
            "priority",
            priority_level,
            server_default=sa.text("'normal'::priority_level"),
            nullable=False,
        ),
        sa.Column(
            "status",
            request_status,
            server_default=sa.text("'waiting'::request_status"),
            nullable=False,
        ),
        sa.Column("reporter_email", sa.String(length=255), nullable=False),
        sa.Column("assigned_staff_id", sa.Uuid(), nullable=True),
        timestamp_column("created_at"),
        timestamp_column("updated_at"),
        sa.Column("completed_at", sa.DateTime(timezone=True), nullable=True),
        sa.ForeignKeyConstraint(["category_id"], ["service_categories.id"]),
        sa.ForeignKeyConstraint(["location_id"], ["locations.id"]),
        sa.ForeignKeyConstraint(["assigned_staff_id"], ["staff.id"]),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("request_code"),
    )
    for column in ("status", "assigned_staff_id", "reporter_email", "created_at"):
        op.create_index(f"ix_service_requests_{column}", "service_requests", [column])
    op.create_index(
        "ix_service_requests_status_created_at", "service_requests", ["status", "created_at"]
    )
    op.create_index(
        "ix_service_requests_assigned_staff_status",
        "service_requests",
        ["assigned_staff_id", "status"],
    )
    op.create_table(
        "request_history",
        uuid_column(),
        sa.Column("request_id", sa.Uuid(), nullable=False),
        sa.Column("action", request_action, nullable=False),
        sa.Column("performed_by", sa.Uuid(), nullable=True),
        sa.Column("target_staff_id", sa.Uuid(), nullable=True),
        sa.Column("old_status", request_status, nullable=True),
        sa.Column("new_status", request_status, nullable=True),
        sa.Column("note", sa.Text(), nullable=True),
        timestamp_column("created_at"),
        sa.ForeignKeyConstraint(["request_id"], ["service_requests.id"]),
        sa.ForeignKeyConstraint(["performed_by"], ["staff.id"]),
        sa.ForeignKeyConstraint(["target_staff_id"], ["staff.id"]),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_table(
        "lost_items",
        uuid_column(),
        sa.Column("item_code", sa.String(length=30), nullable=False),
        sa.Column("report_type", lost_type, nullable=False),
        sa.Column("item_category", sa.String(length=100), nullable=False),
        sa.Column("item_name", sa.String(length=200), nullable=False),
        sa.Column("description", sa.Text(), nullable=True),
        sa.Column("event_datetime", sa.DateTime(timezone=True), nullable=False),
        sa.Column("location_id", sa.Integer(), nullable=True),
        sa.Column("location_detail", sa.String(length=255), nullable=True),
        sa.Column("custody_location", sa.String(length=255), nullable=True),
        sa.Column("reporter_email", sa.String(length=255), nullable=False),
        sa.Column(
            "status",
            lost_status,
            server_default=sa.text("'pending'::lost_status"),
            nullable=False,
        ),
        sa.Column("reviewed_by", sa.Uuid(), nullable=True),
        sa.Column("review_note", sa.Text(), nullable=True),
        timestamp_column("created_at"),
        timestamp_column("updated_at"),
        sa.ForeignKeyConstraint(["location_id"], ["locations.id"]),
        sa.ForeignKeyConstraint(["reviewed_by"], ["staff.id"]),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("item_code"),
    )
    for column in ("report_type", "status", "reporter_email", "created_at"):
        op.create_index(f"ix_lost_items_{column}", "lost_items", [column])
    op.create_index(
        "ix_lost_items_report_type_status", "lost_items", ["report_type", "status"]
    )
    op.create_table(
        "lost_item_history",
        sa.Column("id", sa.Integer(), sa.Identity(), nullable=False),
        sa.Column("lost_item_id", sa.Uuid(), nullable=False),
        sa.Column("staff_id", sa.Uuid(), nullable=True),
        sa.Column("old_status", lost_status, nullable=True),
        sa.Column("new_status", lost_status, nullable=False),
        sa.Column("note", sa.Text(), nullable=True),
        timestamp_column("created_at"),
        sa.ForeignKeyConstraint(["lost_item_id"], ["lost_items.id"]),
        sa.ForeignKeyConstraint(["staff_id"], ["staff.id"]),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(
        "ix_lost_item_history_item_created_at",
        "lost_item_history",
        ["lost_item_id", "created_at"],
    )
    op.create_index(
        "ix_lost_item_history_staff_created_at",
        "lost_item_history",
        ["staff_id", "created_at"],
    )
    op.create_table(
        "lost_claims",
        uuid_column(),
        sa.Column("found_item_id", sa.Uuid(), nullable=False),
        sa.Column("claimant_name", sa.String(length=150), nullable=False),
        sa.Column("claimant_email", sa.String(length=255), nullable=False),
        sa.Column("proof_detail", sa.Text(), nullable=False),
        sa.Column(
            "status",
            claim_status,
            server_default=sa.text("'pending'::claim_status"),
            nullable=False,
        ),
        sa.Column("reviewed_by", sa.Uuid(), nullable=True),
        sa.Column("review_note", sa.Text(), nullable=True),
        timestamp_column("created_at"),
        timestamp_column("updated_at"),
        sa.ForeignKeyConstraint(["found_item_id"], ["lost_items.id"]),
        sa.ForeignKeyConstraint(["reviewed_by"], ["staff.id"]),
        sa.PrimaryKeyConstraint("id"),
    )
    for column in ("found_item_id", "status", "claimant_email"):
        op.create_index(f"ix_lost_claims_{column}", "lost_claims", [column])
    op.create_table(
        "images",
        uuid_column(),
        sa.Column("request_id", sa.Uuid(), nullable=True),
        sa.Column("lost_item_id", sa.Uuid(), nullable=True),
        sa.Column("image_url", sa.Text(), nullable=False),
        sa.Column("image_type", image_type, nullable=True),
        sa.Column("uploaded_by_staff_id", sa.Uuid(), nullable=True),
        timestamp_column("created_at"),
        sa.CheckConstraint(
            "(request_id IS NOT NULL AND lost_item_id IS NULL AND image_type IS NOT NULL) "
            "OR (request_id IS NULL AND lost_item_id IS NOT NULL AND image_type IS NULL)",
            name="image_parent_check",
        ),
        sa.ForeignKeyConstraint(["request_id"], ["service_requests.id"]),
        sa.ForeignKeyConstraint(["lost_item_id"], ["lost_items.id"]),
        sa.ForeignKeyConstraint(["uploaded_by_staff_id"], ["staff.id"]),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_images_request_id", "images", ["request_id"])
    op.create_index("ix_images_lost_item_id", "images", ["lost_item_id"])
    op.create_table(
        "notifications",
        uuid_column(),
        sa.Column("staff_id", sa.Uuid(), nullable=False),
        sa.Column("title", sa.String(length=200), nullable=False),
        sa.Column("message", sa.Text(), nullable=False),
        sa.Column("is_read", sa.Boolean(), server_default=sa.false(), nullable=False),
        timestamp_column("created_at"),
        sa.ForeignKeyConstraint(["staff_id"], ["staff.id"]),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(
        "ix_notifications_staff_is_read", "notifications", ["staff_id", "is_read"]
    )
    op.create_index("ix_notifications_created_at", "notifications", ["created_at"])


def downgrade() -> None:
    """ลบ schema ใหม่และคืนโครงสร้าง staff_accounts เดิม."""
    for table_name in (
        "notifications",
        "images",
        "lost_claims",
        "lost_item_history",
        "lost_items",
        "request_history",
        "service_requests",
        "service_categories",
        "locations",
    ):
        op.drop_table(table_name)

    op.add_column(
        "staff",
        sa.Column("is_active", sa.Boolean(), server_default=sa.true(), nullable=False),
    )
    op.execute("UPDATE staff SET is_active = false WHERE status = 'suspended'")
    op.drop_column("staff", "last_login_at")
    op.drop_column("staff", "status")
    op.alter_column(
        "staff", "full_name", existing_type=sa.String(length=150), type_=sa.String(length=200)
    )
    op.alter_column(
        "staff", "email", existing_type=sa.String(length=255), type_=sa.String(length=320)
    )
    op.alter_column(
        "staff", "staff_code", existing_type=sa.String(length=30), type_=sa.String(length=32)
    )
    op.execute("ALTER INDEX ix_staff_role RENAME TO ix_staff_accounts_role")
    op.execute("ALTER INDEX ix_staff_email RENAME TO ix_staff_accounts_email")
    op.execute("ALTER INDEX ix_staff_staff_code RENAME TO ix_staff_accounts_employee_code")
    op.alter_column("staff", "staff_code", new_column_name="employee_code")
    op.rename_table("staff", "staff_accounts")
    op.execute("ALTER TYPE staff_role RENAME VALUE 'clerk' TO 'coordinator'")

    bind = op.get_bind()
    for enum_type in reversed(new_enums):
        enum_type.drop(bind, checkfirst=True)
