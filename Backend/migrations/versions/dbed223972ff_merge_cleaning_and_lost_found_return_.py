"""merge cleaning and lost-found return status branches

Revision ID: dbed223972ff
Revises: 20260916_0007, 64e6b46fc548
Create Date: 2026-09-17 22:25:18.419520

รวมสองสายที่แตกจาก 20260912_0006 ให้กลับมาเหลือ head เดียว
สาย 20260916_0007 แก้ service_requests ส่วนสาย 64e6b46fc548 แก้ lost_claims
คนละตารางกัน ลำดับก่อนหลังจึงไม่สำคัญ ไฟล์นี้จึงไม่ต้องแก้ schema อะไรเลย
"""

from collections.abc import Sequence

revision: str = "dbed223972ff"
down_revision: tuple[str, ...] = ("20260916_0007", "64e6b46fc548")
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    pass


def downgrade() -> None:
    pass
