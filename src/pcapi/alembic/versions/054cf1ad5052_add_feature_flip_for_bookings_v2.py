"""add_feature_flip_for_bookings_v2

Revision ID: 054cf1ad5052
Revises: 176d931e5dbc
Create Date: 2020-04-23 08:20:23.775514

"""
import enum

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = "054cf1ad5052"
down_revision = "176d931e5dbc"
branch_labels = None
depends_on = None


class FeatureToggle(enum.Enum):
    BOOKINGS_V2 = "Permettre d" "afficher la nouvelle visualisation des réservations d" "un offreur"


def upgrade():
    new_values = (
        "WEBAPP_SIGNUP",
        "DEGRESSIVE_REIMBURSEMENT_RATE",
        "QR_CODE",
        "FULL_OFFERS_SEARCH_WITH_OFFERER_AND_VENUE",
        "SEARCH_ALGOLIA",
        "SEARCH_LEGACY",
        "BENEFICIARIES_IMPORT",
        "SYNCHRONIZE_ALGOLIA",
        "SYNCHRONIZE_ALLOCINE",
        "SYNCHRONIZE_BANK_INFORMATION",
        "SYNCHRONIZE_LIBRAIRES",
        "SYNCHRONIZE_TITELIVE",
        "SYNCHRONIZE_TITELIVE_PRODUCTS",
        "SYNCHRONIZE_TITELIVE_PRODUCTS_DESCRIPTION",
        "SYNCHRONIZE_TITELIVE_PRODUCTS_THUMBS",
        "UPDATE_DISCOVERY_VIEW",
        "UPDATE_BOOKING_USED",
        "RECOMMENDATIONS_WITH_DISCOVERY_VIEW",
        "RECOMMENDATIONS_WITH_DIGITAL_FIRST",
        "RECOMMENDATIONS_WITH_GEOLOCATION",
        "NEW_RIBS_UPLOAD",
        "SAVE_SEEN_OFFERS",
        "BOOKINGS_V2",
    )
    previous_values = (
        "WEBAPP_SIGNUP",
        "DEGRESSIVE_REIMBURSEMENT_RATE",
        "QR_CODE",
        "FULL_OFFERS_SEARCH_WITH_OFFERER_AND_VENUE",
        "SEARCH_ALGOLIA",
        "SEARCH_LEGACY",
        "BENEFICIARIES_IMPORT",
        "SYNCHRONIZE_ALGOLIA",
        "SYNCHRONIZE_ALLOCINE",
        "SYNCHRONIZE_BANK_INFORMATION",
        "SYNCHRONIZE_LIBRAIRES",
        "SYNCHRONIZE_TITELIVE",
        "SYNCHRONIZE_TITELIVE_PRODUCTS",
        "SYNCHRONIZE_TITELIVE_PRODUCTS_DESCRIPTION",
        "SYNCHRONIZE_TITELIVE_PRODUCTS_THUMBS",
        "UPDATE_DISCOVERY_VIEW",
        "UPDATE_BOOKING_USED",
        "RECOMMENDATIONS_WITH_DISCOVERY_VIEW",
        "RECOMMENDATIONS_WITH_DIGITAL_FIRST",
        "RECOMMENDATIONS_WITH_GEOLOCATION",
        "NEW_RIBS_UPLOAD",
        "SAVE_SEEN_OFFERS",
    )

    previous_enum = sa.Enum(*previous_values, name="featuretoggle")
    new_enum = sa.Enum(*new_values, name="featuretoggle")
    temporary_enum = sa.Enum(*new_values, name="tmp_featuretoggle")

    temporary_enum.create(op.get_bind(), checkfirst=False)
    op.execute("ALTER TABLE feature ALTER COLUMN name TYPE tmp_featuretoggle" " USING name::text::tmp_featuretoggle")
    previous_enum.drop(op.get_bind(), checkfirst=False)
    new_enum.create(op.get_bind(), checkfirst=False)
    op.execute("ALTER TABLE feature ALTER COLUMN name TYPE featuretoggle" " USING name::text::featuretoggle")
    op.execute(
        """
            INSERT INTO feature (name, description, "isActive")
            VALUES ('%s', '%s', FALSE);
            """
        % (FeatureToggle.BOOKINGS_V2.name, FeatureToggle.BOOKINGS_V2.value)
    )
    temporary_enum.drop(op.get_bind(), checkfirst=False)


def downgrade():
    new_values = (
        "WEBAPP_SIGNUP",
        "DEGRESSIVE_REIMBURSEMENT_RATE",
        "QR_CODE",
        "FULL_OFFERS_SEARCH_WITH_OFFERER_AND_VENUE",
        "SEARCH_ALGOLIA",
        "SEARCH_LEGACY",
        "BENEFICIARIES_IMPORT",
        "SYNCHRONIZE_ALGOLIA",
        "SYNCHRONIZE_ALLOCINE",
        "SYNCHRONIZE_BANK_INFORMATION",
        "SYNCHRONIZE_LIBRAIRES",
        "SYNCHRONIZE_TITELIVE",
        "SYNCHRONIZE_TITELIVE_PRODUCTS",
        "SYNCHRONIZE_TITELIVE_PRODUCTS_DESCRIPTION",
        "SYNCHRONIZE_TITELIVE_PRODUCTS_THUMBS",
        "UPDATE_DISCOVERY_VIEW",
        "UPDATE_BOOKING_USED",
        "RECOMMENDATIONS_WITH_DISCOVERY_VIEW",
        "RECOMMENDATIONS_WITH_DIGITAL_FIRST",
        "RECOMMENDATIONS_WITH_GEOLOCATION",
        "NEW_RIBS_UPLOAD",
        "SAVE_SEEN_OFFERS",
    )
    previous_values = (
        "WEBAPP_SIGNUP",
        "DEGRESSIVE_REIMBURSEMENT_RATE",
        "QR_CODE",
        "FULL_OFFERS_SEARCH_WITH_OFFERER_AND_VENUE",
        "SEARCH_ALGOLIA",
        "SEARCH_LEGACY",
        "BENEFICIARIES_IMPORT",
        "SYNCHRONIZE_ALGOLIA",
        "SYNCHRONIZE_ALLOCINE",
        "SYNCHRONIZE_BANK_INFORMATION",
        "SYNCHRONIZE_LIBRAIRES",
        "SYNCHRONIZE_TITELIVE",
        "SYNCHRONIZE_TITELIVE_PRODUCTS",
        "SYNCHRONIZE_TITELIVE_PRODUCTS_DESCRIPTION",
        "SYNCHRONIZE_TITELIVE_PRODUCTS_THUMBS",
        "UPDATE_DISCOVERY_VIEW",
        "UPDATE_BOOKING_USED",
        "RECOMMENDATIONS_WITH_DISCOVERY_VIEW",
        "RECOMMENDATIONS_WITH_DIGITAL_FIRST",
        "RECOMMENDATIONS_WITH_GEOLOCATION",
        "NEW_RIBS_UPLOAD",
        "SAVE_SEEN_OFFERS",
        "BOOKINGS_V2",
    )

    previous_enum = sa.Enum(*previous_values, name="featuretoggle")
    new_enum = sa.Enum(*new_values, name="featuretoggle")
    temporary_enum = sa.Enum(*new_values, name="tmp_featuretoggle")

    op.execute("DELETE FROM feature WHERE name = 'BOOKINGS_V2'")
    temporary_enum.create(op.get_bind(), checkfirst=False)
    op.execute("ALTER TABLE feature ALTER COLUMN name TYPE tmp_featuretoggle" " USING name::text::tmp_featuretoggle")
    previous_enum.drop(op.get_bind(), checkfirst=False)
    new_enum.create(op.get_bind(), checkfirst=False)
    op.execute("ALTER TABLE feature ALTER COLUMN name TYPE featuretoggle" " USING name::text::featuretoggle")
    temporary_enum.drop(op.get_bind(), checkfirst=False)
