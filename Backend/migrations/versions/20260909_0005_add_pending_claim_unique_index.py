"""Add partial unique index to stop duplicate pending claims from racing.

Revision ID: 20260909_0005
Revises: 20260815_0004
Create Date: 2026-09-09
"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

revision: str = "20260909_0005"
down_revision: str | None = "20260815_0004"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    """กัน race condition: อีเมลเดียวยื่น claim pending ซ้ำต่อประกาศเดียวกันไม่ได้.

    service ตรวจซ้ำด้วย SELECT ก่อน INSERT อยู่แล้ว แต่นั่นรับประกันความถูกต้องไม่ได้
    ถ้าสอง request เข้ามาพร้อมกัน (เช่น ผู้ใช้กดปุ่มส่งสองครั้งติด ๆ) ทั้งคู่จะเห็นผล
    SELECT ว่า "ยังไม่ซ้ำ" แล้วบันทึกผ่านทั้งสองแถว — ต้องมี constraint ที่ DB จริง
    ๆ เท่านั้นถึงจะการันตีได้

    ใช้ partial index (WHERE status = 'pending') แทน unique ธรรมดา เพราะคนที่เคยถูก
    reject ต้องยื่นคำขอใหม่ได้ ถ้าทำเป็น unique เต็มแถวจะบล็อกคนกลุ่มนี้ไปตลอด
    """
    op.create_index(
        "uq_lost_claims_pending_per_email",
        "lost_claims",
        ["found_item_id", "claimant_email"],
        unique=True,
        postgresql_where=sa.text("status = 'pending'"),
    )


def downgrade() -> None:
    op.drop_index("uq_lost_claims_pending_per_email", table_name="lost_claims")
