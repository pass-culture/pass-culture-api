"""Feature flip send invites

Revision ID: 6983e5765f4f
Revises: e442fb5ac4e6
Create Date: 2021-05-21 16:53:51.706974

"""
from pcapi.models import feature


# revision identifiers, used by Alembic.
revision = "6983e5765f4f"
down_revision = "e442fb5ac4e6"
branch_labels = None
depends_on = None


def upgrade() -> None:
    feature.add_feature_to_database(feature.FeatureToggle.USE_NATIVE_EMAILS_IN_ID_CHECK_INVITES)
    feature.add_feature_to_database(feature.FeatureToggle.AUTOMATICALLY_SEND_ID_CHECK_INVITES)


def downgrade() -> None:
    feature.remove_feature_from_database(feature.FeatureToggle.AUTOMATICALLY_SEND_ID_CHECK_INVITES)
    feature.remove_feature_from_database(feature.FeatureToggle.USE_NATIVE_EMAILS_IN_ID_CHECK_INVITES)
