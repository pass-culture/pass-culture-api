"""add_code_to_venue_type

Revision ID: cd3392bcd798
Revises: 19b36a0b880a
Create Date: 2021-08-02 12:00:40.814484

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = "cd3392bcd798"
down_revision = "ff887e7b4f89"
branch_labels = None
depends_on = None


def upgrade():
    op.add_column("venue_type", sa.Column("code", sa.String(length=64), nullable=True))


def downgrade():
    op.drop_column("venue_type", "code")
