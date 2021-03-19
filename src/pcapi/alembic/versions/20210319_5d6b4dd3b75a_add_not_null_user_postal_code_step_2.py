"""add_not_null_user_postal_code_step_2

Revision ID: 5d6b4dd3b75a
Revises: 36beca92440d
Create Date: 2021-03-19 10:31:23.141677

"""
from alembic import op


# revision identifiers, used by Alembic.
revision = "5d6b4dd3b75a"
down_revision = "36beca92440d"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.execute('ALTER TABLE "user" VALIDATE CONSTRAINT postal_code_not_null_constraint;')


def downgrade() -> None:
    pass
