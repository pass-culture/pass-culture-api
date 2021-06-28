"""add_educational_institution_to_deposit_table

Revision ID: a80cfa78992a
Revises: d49958abc723
Create Date: 2021-06-25 16:03:13.179897

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = "e80cfa78992a"
down_revision = "f6f7e23ac042"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column(
        "deposit",
        sa.Column(
            "educationalInstitutionId",
            sa.BigInteger,
            index=True,
            nullable=True,
        ),
    )
    op.create_foreign_key(
        "deposit_eductionalInstitutionId_fkey",
        "deposit",
        "educational_institution",
        ["educationalInstitutionId"],
        ["id"],
    )


def downgrade() -> None:
    op.drop_constraint("deposit_eductionalInstitutionId_fkey", "deposit", type_="foreignkey")
    op.drop_column("deposit", "educationalInstitutionId")
