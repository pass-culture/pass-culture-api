"""add_accessibility_to_venue

Revision ID: 43d69b38770f
Revises: c016332e7bfb
Create Date: 2021-08-06 18:51:26.457203

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = "43d69b38770f"
down_revision = "c016332e7bfb"
branch_labels = None
depends_on = None


def upgrade():
    op.add_column("venue", sa.Column("audioDisabilityCompliant", sa.Boolean(), nullable=True))
    op.add_column("venue", sa.Column("mentalDisabilityCompliant", sa.Boolean(), nullable=True))
    op.add_column("venue", sa.Column("motorDisabilityCompliant", sa.Boolean(), nullable=True))
    op.add_column("venue", sa.Column("visualDisabilityCompliant", sa.Boolean(), nullable=True))


def downgrade():
    op.drop_column("venue", "visualDisabilityCompliant")
    op.drop_column("venue", "motorDisabilityCompliant")
    op.drop_column("venue", "mentalDisabilityCompliant")
    op.drop_column("venue", "audioDisabilityCompliant")
