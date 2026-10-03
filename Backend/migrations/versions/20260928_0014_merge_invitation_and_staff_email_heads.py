"""Merge invitation records with the email-only staff migration history.

Revision ID: 20260928_0014
Revises: 20260928_0010, 20260924_0012
Create Date: 2026-09-28
"""

from collections.abc import Sequence

revision: str = "20260928_0014"
down_revision: tuple[str, str] = ("20260928_0010", "20260924_0012")
branch_labels: str | Sequence[str] | None = None
depends_on: str | None = None


def upgrade() -> None:
    """Both parent branches have already applied their schema changes."""


def downgrade() -> None:
    """The parents can be downgraded independently after this merge marker."""
