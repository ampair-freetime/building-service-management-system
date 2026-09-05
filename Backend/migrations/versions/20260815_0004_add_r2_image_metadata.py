"""Add R2 object metadata and future retention fields.

Revision ID: 20260815_0004
Revises: 20260812_0003
Create Date: 2026-08-15
"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

revision: str = "20260815_0004"
down_revision: str | None = "20260812_0003"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    """เก็บ stable object key และเตรียม metadata สำหรับ R2/retention."""
    op.alter_column("images", "image_url", new_column_name="object_key")
    op.add_column(
        "images",
        sa.Column(
            "storage_provider",
            sa.String(length=20),
            server_default="r2",
            nullable=False,
        ),
    )
    op.add_column(
        "images",
        sa.Column("bucket_name", sa.String(length=255), nullable=True),
    )
    op.add_column(
        "images",
        sa.Column("content_type", sa.String(length=100), nullable=True),
    )
    op.add_column("images", sa.Column("size_bytes", sa.Integer(), nullable=True))
    op.add_column(
        "images",
        sa.Column("etag", sa.String(length=128), nullable=True),
    )
    op.add_column("images", sa.Column("width", sa.Integer(), nullable=True))
    op.add_column("images", sa.Column("height", sa.Integer(), nullable=True))
    op.add_column(
        "images",
        sa.Column("purge_after", sa.DateTime(timezone=True), nullable=True),
    )
    op.add_column(
        "images",
        sa.Column("deleted_at", sa.DateTime(timezone=True), nullable=True),
    )
    op.create_index("ix_images_purge_after", "images", ["purge_after"])

    op.add_column(
        "lost_items",
        sa.Column("private_verification_detail", sa.Text(), nullable=True),
    )
    op.add_column(
        "lost_items",
        sa.Column("expires_at", sa.DateTime(timezone=True), nullable=True),
    )
    op.add_column(
        "lost_items",
        sa.Column("archived_at", sa.DateTime(timezone=True), nullable=True),
    )
    op.add_column(
        "lost_items",
        sa.Column("deleted_at", sa.DateTime(timezone=True), nullable=True),
    )
    op.create_index("ix_lost_items_expires_at", "lost_items", ["expires_at"])


def downgrade() -> None:
    """ย้อนกลับ metadata โดยคืนชื่อ image_url เดิม."""
    op.drop_index("ix_lost_items_expires_at", table_name="lost_items")
    op.drop_column("lost_items", "deleted_at")
    op.drop_column("lost_items", "archived_at")
    op.drop_column("lost_items", "expires_at")
    op.drop_column("lost_items", "private_verification_detail")

    op.drop_index("ix_images_purge_after", table_name="images")
    op.drop_column("images", "deleted_at")
    op.drop_column("images", "purge_after")
    op.drop_column("images", "height")
    op.drop_column("images", "width")
    op.drop_column("images", "etag")
    op.drop_column("images", "size_bytes")
    op.drop_column("images", "content_type")
    op.drop_column("images", "bucket_name")
    op.drop_column("images", "storage_provider")
    op.alter_column("images", "object_key", new_column_name="image_url")
