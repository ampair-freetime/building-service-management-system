"""Human-readable claim codes and guest-facing staff messages."""
from alembic import op
import sqlalchemy as sa

revision = "20261008_0021"
down_revision = "20261007_0020"
branch_labels = None
depends_on = None


def upgrade():
    op.add_column("lost_claims", sa.Column("claim_code", sa.String(30), nullable=True))
    op.add_column("lost_claims", sa.Column("staff_message", sa.Text(), nullable=True))
    # Use each row's original creation date in Bangkok, including legacy claims.
    op.execute("""UPDATE lost_claims SET claim_code = 'CLM-' ||
        to_char(created_at AT TIME ZONE 'Asia/Bangkok', 'YYYYMMDD') || '-' ||
        upper(left(replace(id::text, '-', ''), 8))""")
    # Resolve rare short-prefix collisions deterministically before enforcing uniqueness.
    op.execute("""WITH ranked AS (
        SELECT id, row_number() OVER (PARTITION BY claim_code ORDER BY id) AS n
        FROM lost_claims
    ) UPDATE lost_claims c SET claim_code = c.claim_code || '-' || ranked.n::text
      FROM ranked WHERE c.id = ranked.id AND ranked.n > 1""")
    op.execute("""UPDATE lost_claims SET staff_message = review_note
        WHERE status IN ('rejected', 'additional_info_required')""")
    op.alter_column("lost_claims", "claim_code", nullable=False)
    op.create_unique_constraint("uq_lost_claims_claim_code", "lost_claims", ["claim_code"])


def downgrade():
    op.drop_constraint("uq_lost_claims_claim_code", "lost_claims", type_="unique")
    op.drop_column("lost_claims", "staff_message")
    op.drop_column("lost_claims", "claim_code")
