from collections.abc import Sequence

from alembic import op
import sqlalchemy as sa


revision: str = "5a266dcc5282"
down_revision: str | None = "20260912_0006"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    return_status_enum = sa.Enum(
        "pending",
        "ready_for_pickup",
        "returned",
        name="return_status",
    )

    return_status_enum.create(op.get_bind(), checkfirst=True)

    op.add_column(
        "lost_claims",
        sa.Column(
            "return_status",
            return_status_enum,
            nullable=True,
        ),
    )


def downgrade() -> None:
    op.drop_column(
        "lost_claims",
        "return_status",
    )

    return_status_enum = sa.Enum(
        "pending",
        "ready_for_pickup",
        "returned",
        name="return_status",
    )

    return_status_enum.drop(op.get_bind(), checkfirst=True)
