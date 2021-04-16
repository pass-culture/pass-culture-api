"""enable phone validation feature

Revision ID: 40754eda1d0f
Revises: 926c8df53762
Create Date: 2021-04-21 07:34:25.619768

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = "40754eda1d0f"
down_revision = "926c8df53762"
branch_labels = None
depends_on = None


def upgrade() -> None:
    # ### commands auto generated by Alembic ###
    op.alter_column(
        "stock", "dnBookedQuantity", existing_type=sa.BIGINT(), nullable=False, existing_server_default=sa.text("0")
    )
    # ### end Alembic commands ###


def downgrade() -> None:
    # ### commands auto generated by Alembic ###
    op.alter_column(
        "stock", "dnBookedQuantity", existing_type=sa.BIGINT(), nullable=True, existing_server_default=sa.text("0")
    )
    # ### end Alembic commands ###
