"""add_not_null_user_postal_code_step_4

Revision ID: c42ad457c577
Revises: b58ad7465931
Create Date: 2021-03-19 10:31:28.418260

"""
from alembic import op


# revision identifiers, used by Alembic.
revision = "c42ad457c577"
down_revision = "b58ad7465931"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.drop_constraint("postal_code_not_null_constraint", table_name="user")


def downgrade() -> None:
    op.execute(
        """
            ALTER TABLE "user" ADD CONSTRAINT postal_code_not_null_constraint CHECK ("postalCode" IS NOT NULL) NOT VALID;
        """
    )
