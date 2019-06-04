"""Change length of Deposit.source column

Revision ID: cff9e82d0558
Revises: c41e9543e851
Create Date: 2019-05-21 13:49:08.219046

"""
import sqlalchemy as sa
from alembic import op

# revision identifiers, used by Alembic.
revision = 'cff9e82d0558'
down_revision = 'c41e9543e851'
branch_labels = None
depends_on = None


def upgrade():
    op.alter_column(
        'deposit', 'source',
        existing_type=sa.VARCHAR(length=12),
        type_=sa.String(length=300),
        existing_nullable=False
    )

    op.execute("""
    UPDATE deposit
    SET source = 'import par fichier CSV'
    WHERE source = 'activation';
    """)


def downgrade():
    op.execute("""
    UPDATE deposit
    SET source = 'activation'
    WHERE source = 'import par fichier CSV';
    """)

    op.alter_column(
        'deposit', 'source',
        existing_type=sa.VARCHAR(length=300),
        type_=sa.String(length=12),
        existing_nullable=False
    )
