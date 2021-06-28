"""deposit_make_userId_nullable

Revision ID: 56f7e23ac042
Revises: e80cfa78992a
Create Date: 2021-06-25 17:24:43.272904

"""
from alembic import op


# revision identifiers, used by Alembic.
revision = "f6f7e23ac042"
down_revision = "d49958abc723"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.alter_column("deposit", "userId", nullable=True)


def downgrade() -> None:
    op.alter_column("deposit", "userId", nullable=False)
