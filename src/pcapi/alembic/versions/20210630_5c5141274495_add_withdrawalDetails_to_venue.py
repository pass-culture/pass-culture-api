"""Add

Revision ID: 5c5141274495
Revises: 6c410aedecbd
Create Date: 2021-06-30 13:08:41.535846

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = "5c5141274495"
down_revision = "6c410aedecbd"
branch_labels = None
depends_on = None


def upgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    op.add_column("venue", sa.Column("withdrawalDetails", sa.Text(), nullable=True))
    # ### end Alembic commands ###


def downgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    op.drop_column("venue", "withdrawalDetails")
    # ### end Alembic commands ###
