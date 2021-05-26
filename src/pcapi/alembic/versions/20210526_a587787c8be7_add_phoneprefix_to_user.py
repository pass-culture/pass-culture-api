"""add_phonePrefix_to_user

Revision ID: a587787c8be7
Revises: 963e6e163cf0
Create Date: 2021-05-26 13:47:55.391134

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = "a587787c8be7"
down_revision = "963e6e163cf0"
branch_labels = None
depends_on = None


def upgrade():
    op.add_column("user", sa.Column("phonePrefix", sa.String(length=10), nullable=True))


def downgrade():
    op.drop_column("user", "phonePrefix")
