"""สร้าง enum บทบาทและตารางบัญชีพนักงาน.

Revision ID: 20260806_0001
Revises:
Create Date: 2026-08-06
"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

# ข้อมูล revision ช่วยให้ Alembic เรียงลำดับ migration ได้ถูกต้อง
revision: str = "20260806_0001"
down_revision: str | None = None
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    """เพิ่มชนิดข้อมูลบทบาท ตารางบัญชี และ index สำหรับการค้นหา."""
    # PostgreSQL enum บังคับให้ role ในฐานข้อมูลมีได้เฉพาะ 4 ค่านี้
    staff_role = postgresql.ENUM(
        "housekeeper",
        "technician",
        "coordinator",
        "admin",
        name="staff_role",
        create_type=False,
    )
    staff_role.create(op.get_bind(), checkfirst=True)

    op.create_table(
        "staff_accounts",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("employee_code", sa.String(length=32), nullable=False),
        sa.Column("email", sa.String(length=320), nullable=False),
        sa.Column("full_name", sa.String(length=200), nullable=False),
        # ตารางเก็บเฉพาะ password_hash ไม่เคยเก็บรหัสผ่านจริง
        sa.Column("password_hash", sa.String(length=255), nullable=False),
        sa.Column("role", staff_role, nullable=False),
        sa.Column("is_active", sa.Boolean(), server_default=sa.true(), nullable=False),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.func.now(),
            nullable=False,
        ),
        sa.Column(
            "updated_at",
            sa.DateTime(timezone=True),
            server_default=sa.func.now(),
            nullable=False,
        ),
        sa.PrimaryKeyConstraint("id"),
    )

    # unique index ช่วยค้นหาเร็วและป้องกันอีเมล/รหัสพนักงานซ้ำในระดับฐานข้อมูล
    op.create_index(
        op.f("ix_staff_accounts_employee_code"),
        "staff_accounts",
        ["employee_code"],
        unique=True,
    )
    op.create_index(
        op.f("ix_staff_accounts_email"),
        "staff_accounts",
        ["email"],
        unique=True,
    )
    op.create_index(
        op.f("ix_staff_accounts_role"),
        "staff_accounts",
        ["role"],
        unique=False,
    )


def downgrade() -> None:
    """ย้อน migration โดยลบ index ตาราง และ enum ตามลำดับ."""
    op.drop_index(op.f("ix_staff_accounts_role"), table_name="staff_accounts")
    op.drop_index(op.f("ix_staff_accounts_email"), table_name="staff_accounts")
    op.drop_index(op.f("ix_staff_accounts_employee_code"), table_name="staff_accounts")
    op.drop_table("staff_accounts")
    postgresql.ENUM(name="staff_role").drop(op.get_bind(), checkfirst=True)
