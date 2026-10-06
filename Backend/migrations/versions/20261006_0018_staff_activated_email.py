"""Track the email address that completed staff activation."""
from alembic import op
import sqlalchemy as sa

revision = "20261006_0018"
down_revision = "20261006_0017"
branch_labels = None
depends_on = None


def upgrade():
    op.add_column("staff", sa.Column("activated_email", sa.String(255), nullable=True))
    op.execute("UPDATE staff SET activated_email = email WHERE password_changed_at IS NOT NULL")


def downgrade():
    op.drop_column("staff", "activated_email")
