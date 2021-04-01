"""add_feature_flag_mobile_app_up

Revision ID: ec634c3af832
Revises: 202ae94f2c8f
Create Date: 2021-04-01 11:59:23.069031

"""
from alembic import op
from sqlalchemy import text

from pcapi.models.feature import FeatureToggle


# revision identifiers, used by Alembic.
revision = "ec634c3af832"
down_revision = "202ae94f2c8f"
branch_labels = None
depends_on = None


def upgrade() -> None:
    feature = FeatureToggle.MOBILE_APP_UP
    op.execute(
        text("""INSERT INTO feature (name, description, "isActive") VALUES (:name, :value, true)""").bindparams(
            name=feature.name, value=feature.value
        )
    )


def downgrade() -> None:
    feature = FeatureToggle.MOBILE_APP_UP
    op.execute(text("""DELETE FROM feature WHERE name = :name""").bindparams(name=feature.name))
