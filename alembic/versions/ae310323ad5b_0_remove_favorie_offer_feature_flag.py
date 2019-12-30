"""remove_favorite_offer_feature_flag

Revision ID: ae310323ad5b
Revises: 2ae0f4147390
Create Date: 2019-12-30 12:55:15.150226

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
from models.feature import FeatureToggle

revision = 'ae310323ad5b'
down_revision = '2ae0f4147390'
branch_labels = None
depends_on = None

previous_values = ('WEBAPP_SIGNUP', 'FAVORITE_OFFER', 'DEGRESSIVE_REIMBURSEMENT_RATE', 'QR_CODE')
new_values = ('WEBAPP_SIGNUP', 'DEGRESSIVE_REIMBURSEMENT_RATE', 'QR_CODE')

previous_enum = sa.Enum(*previous_values, name='featuretoggle')
new_enum = sa.Enum(*new_values, name='featuretoggle')
temporary_enum = sa.Enum(*new_values, name='tmp_featuretoggle')


def upgrade():
    op.execute("DELETE FROM feature WHERE name = 'FAVORITE_OFFER'")


def downgrade():
    temporary_enum.create(op.get_bind(), checkfirst=False)
    op.execute('ALTER TABLE feature ALTER COLUMN name TYPE tmp_featuretoggle'
               ' USING name::text::tmp_featuretoggle')
    previous_enum.drop(op.get_bind(), checkfirst=False)
    new_enum.create(op.get_bind(), checkfirst=False)
    op.execute('ALTER TABLE feature ALTER COLUMN name TYPE featuretoggle'
               ' USING name::text::featuretoggle')
    op.execute("""
                INSERT INTO feature (name, description, "isActive")
                VALUES ('%s', '%s', FALSE);
                """ % (FeatureToggle.DUO_OFFER.name, FeatureToggle.DUO_OFFER.value))
    temporary_enum.drop(op.get_bind(), checkfirst=False)

