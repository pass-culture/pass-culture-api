"""Add isSoftDeleted Boolean to event_occurence and remove isActive

Revision ID: a462a0208015
Revises: 10ea71b5a60b
Create Date: 2018-09-06 12:20:50.005580

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = 'a462a0208015'
down_revision = '10ea71b5a60b'
branch_labels = None
depends_on = None


def upgrade():
    op.add_column('event_occurence', sa.Column('isSoftDeleted', sa.BOOLEAN, nullable=False, server_default=expression.false()))
    op.drop_column('event_occurence', 'isActive')


def downgrade():
    op.drop_column('event_occurence', 'isSoftDeleted')
    op.add_column('event_occurence', sa.Column('isActive', sa.BOOLEAN, nullable=False, server_default=expression.true()))
