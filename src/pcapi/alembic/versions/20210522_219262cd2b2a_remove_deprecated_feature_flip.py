"""Remove deprecated feature flips

Revision ID: 219262cd2b2a
Revises: 865dbe4bec27
Create Date: 2021-05-09 13:54:24.235104

"""
import enum

from pcapi.models import feature


# revision identifiers, used by Alembic.
revision = "219262cd2b2a"
down_revision = "865dbe4bec27"
branch_labels = None
depends_on = None


class DeprecatedFeatureToggle(enum.Enum):
    FNAC_SYNCHRONIZATION_V2 = "Active la synchronisation FNAC v2 : synchronisation par batch"


FLAG = DeprecatedFeatureToggle.FNAC_SYNCHRONIZATION_V2


def upgrade():
    feature.remove_feature_from_database(FLAG)


def downgrade():
    feature.add_feature_to_database(FLAG)
