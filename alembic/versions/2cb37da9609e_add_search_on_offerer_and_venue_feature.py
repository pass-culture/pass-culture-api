"""add_search_on_offerer_and_venue_feature

Revision ID: 2cb37da9609e
Revises: 75f2ccf2be82
Create Date: 2019-12-20 16:27:25.904572

"""
import sqlalchemy as sa
from alembic import op

# revision identifiers, used by Alembic.
from models.feature import FeatureToggle

revision = '2cb37da9609e'
down_revision = '75f2ccf2be82'
branch_labels = None
depends_on = None

previous_values = ('WEBAPP_SIGNUP', 'FAVORITE_OFFER', 'DEGRESSIVE_REIMBURSEMENT_RATE', 'DUO_OFFER', 'QR_CODE')
new_values = ('WEBAPP_SIGNUP', 'FAVORITE_OFFER', 'DEGRESSIVE_REIMBURSEMENT_RATE', 'DUO_OFFER', 'QR_CODE',
              'FULL_OFFERS_SEARCH_WITH_OFFERER_AND_VENUE')

previous_enum = sa.Enum(*previous_values, name='featuretoggle')
new_enum = sa.Enum(*new_values, name='featuretoggle')
temporary_enum = sa.Enum(*new_values, name='tmp_featuretoggle')


def upgrade():
    temporary_enum.create(op.get_bind(), checkfirst=False)
    op.execute('ALTER TABLE feature ALTER COLUMN name TYPE TMP_FEATURETOGGLE'
               ' USING name::TEXT::TMP_FEATURETOGGLE')
    previous_enum.drop(op.get_bind(), checkfirst=False)
    new_enum.create(op.get_bind(), checkfirst=False)
    op.execute('ALTER TABLE feature ALTER COLUMN name TYPE FEATURETOGGLE'
               ' USING name::TEXT::FEATURETOGGLE')
    op.execute("""
        INSERT INTO feature (name, description, "isActive")
        VALUES ('%s', '%s', TRUE);
        """ % (FeatureToggle.FULL_OFFERS_SEARCH_WITH_OFFERER_AND_VENUE.name,
               FeatureToggle.FULL_OFFERS_SEARCH_WITH_OFFERER_AND_VENUE.value))
    temporary_enum.drop(op.get_bind(), checkfirst=False)


def downgrade():
    temporary_enum.create(op.get_bind(), checkfirst=False)
    op.execute('ALTER TABLE feature ALTER COLUMN name TYPE TMP_FEATURETOGGLE'
               ' USING name::TEXT::TMP_FEATURETOGGLE')
    new_enum.drop(op.get_bind(), checkfirst=False)
    previous_enum.create(op.get_bind(), checkfirst=False)
    op.execute("DELETE FROM feature WHERE name = 'FULL_OFFERS_SEARCH_WITH_OFFERER_AND_VENUE'")
    op.execute('ALTER TABLE feature ALTER COLUMN name TYPE FEATURETOGGLE'
               ' USING name::TEXT::FEATURETOGGLE')
    temporary_enum.drop(op.get_bind(), checkfirst=False)
