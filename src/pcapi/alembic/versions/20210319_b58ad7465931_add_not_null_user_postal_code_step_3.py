"""add_not_null_user_postal_code_step_3

Revision ID: b58ad7465931
Revises: 5d6b4dd3b75a
Create Date: 2021-03-19 10:31:25.767147

"""
from alembic import op


# revision identifiers, used by Alembic.
revision = "b58ad7465931"
down_revision = "5d6b4dd3b75a"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.alter_column("user", "postalCode", nullable=False)


def downgrade() -> None:
    op.alter_column("user", "postalCode", nullable=True)
