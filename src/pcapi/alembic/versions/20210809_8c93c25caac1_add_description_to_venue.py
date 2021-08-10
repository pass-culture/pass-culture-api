"""add_description_to_venue

Revision ID: 8c93c25caac1
Revises: 1c5bec8d2aec
Create Date: 2021-08-09 18:59:37.025464

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = "8c93c25caac1"
down_revision = "1c5bec8d2aec"
branch_labels = None
depends_on = None


def upgrade():
    op.add_column("venue", sa.Column("description", sa.Text(), nullable=True))


def downgrade():
    op.drop_column("venue", "description")
