"""add_not_null_user_postal_code_step_1

Revision ID: 36beca92440d
Revises: 0f9f0a4ae98d
Create Date: 2021-03-19 10:31:19.634258

"""
from alembic import op


# revision identifiers, used by Alembic.
revision = "36beca92440d"
down_revision = "0f9f0a4ae98d"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.execute(
        """
            ALTER TABLE "user" ADD CONSTRAINT postal_code_not_null_constraint CHECK ("postalCode" IS NOT NULL) NOT VALID;
        """
    )


def downgrade() -> None:
    op.drop_constraint("postal_code_not_null_constraint", table_name="user")
