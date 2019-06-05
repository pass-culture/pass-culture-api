"""Add has filled cultural survey to user

Revision ID: ebb2366cbf96
Revises: cff9e82d0558
Create Date: 2019-06-04 12:19:06.468967

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.sql import expression


# revision identifiers, used by Alembic.
revision = 'ebb2366cbf96'
down_revision = 'cff9e82d0558'
branch_labels = None
depends_on = None


def upgrade():
    op.add_column('user', sa.Column('hasFilledCulturalSurvey', sa.BOOLEAN, server_default=expression.false()))


def downgrade():
    op.drop_column('user', 'hasFilledCulturalSurvey')
