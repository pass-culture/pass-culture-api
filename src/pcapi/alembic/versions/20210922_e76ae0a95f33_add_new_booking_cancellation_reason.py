"""Add new booking cancellation reason enum value
"""
from alembic import op


# revision identifiers, used by Alembic.
revision = "e76ae0a95f33"
down_revision = "1c48ca792f7d"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.execute("ALTER TYPE cancellation_reason ADD VALUE 'REFUND_CANCELLED'")


def downgrade() -> None:
    op.execute("ALTER TYPE cancellation_reason RENAME TO cancellation_reason_old")
    op.execute(
        "CREATE TYPE cancellation_reason AS ENUM('OFFERER','BENEFICIARY','EXPIRED','FRAUD','REFUSED_BY_INSTITUTE')"
    )
    op.execute(
        (
            "ALTER TABLE booking ALTER COLUMN cancellationReason TYPE cancellation_reason USING "
            "status::text::cancellation_reason"
        )
    )
    op.execute("DROP TYPE cancellation_reason_old")
