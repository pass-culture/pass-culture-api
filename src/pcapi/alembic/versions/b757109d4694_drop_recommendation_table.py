"""drop_recommendation_table

Revision ID: b757109d4694
Revises: 1196c69e1385
Create Date: 2021-01-08 14:30:11.459680

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = "b757109d4694"
down_revision = "1196c69e1385"
branch_labels = None
depends_on = None


def upgrade():
    op.drop_column("booking", "recommendationId")
    op.drop_table("recommendation")


def downgrade():
    # ### commands auto generated by Alembic ###
    op.create_table(
        "recommendation",
        sa.Column("id", sa.BigInteger(), autoincrement=True, nullable=False),
        sa.Column("userId", sa.BigInteger(), nullable=False),
        sa.Column("mediationId", sa.BigInteger(), nullable=True),
        sa.Column("offerId", sa.BigInteger(), nullable=True),
        sa.Column("shareMedium", sa.String(length=20), nullable=True),
        sa.Column("dateCreated", sa.DateTime(), nullable=False),
        sa.Column("dateUpdated", sa.DateTime(), nullable=False),
        sa.Column("dateRead", sa.DateTime(), nullable=True),
        sa.Column("isClicked", sa.Boolean(), server_default=sa.text("false"), nullable=False),
        sa.Column("isFirst", sa.Boolean(), server_default=sa.text("false"), nullable=False),
        sa.Column("search", sa.String(), nullable=True),
        sa.ForeignKeyConstraint(
            ["mediationId"],
            ["mediation.id"],
        ),
        sa.ForeignKeyConstraint(
            ["offerId"],
            ["offer.id"],
        ),
        sa.ForeignKeyConstraint(
            ["userId"],
            ["user.id"],
        ),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(op.f("ix_recommendation_mediationId"), "recommendation", ["mediationId"], unique=False)
    op.create_index(op.f("ix_recommendation_offerId"), "recommendation", ["offerId"], unique=False)
    op.create_index(op.f("ix_recommendation_userId"), "recommendation", ["userId"], unique=False)
    op.add_column("booking", sa.Column("recommendationId", sa.BigInteger(), nullable=True))
    op.create_index(op.f("ix_booking_recommendationId"), "booking", ["recommendationId"], unique=False)
    op.create_foreign_key(None, "booking", "recommendation", ["recommendationId"], ["id"])
    # ### end Alembic commands ###
