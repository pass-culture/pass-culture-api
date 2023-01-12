"""remove_has_allowed_reco

Revision ID: ccf69bc028ef
Revises: 84cab0060952
Create Date: 2021-04-12 16:06:06.909312

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = "ccf69bc028ef"
down_revision = "84cab0060952"
branch_labels = None
depends_on = None


def upgrade():
    # ### commands auto generated by Alembic ###
    op.drop_column("user", "hasAllowedRecommendations")
    # ### end Alembic commands ###


def downgrade():
    # ### commands auto generated by Alembic ###
    op.add_column(
        "user",
        sa.Column(
            "hasAllowedRecommendations",
            sa.BOOLEAN(),
            server_default=sa.text("false"),
            autoincrement=False,
            nullable=False,
        ),
    )
    # ### end Alembic commands ###