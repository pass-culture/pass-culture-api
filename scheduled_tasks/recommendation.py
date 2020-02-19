import os

from models import DiscoveryView
from models.feature import FeatureToggle
from scheduled_tasks.decorators import log_cron, cron_context, cron_require_feature

RECO_VIEW_REFRESH_FREQUENCY = os.environ.get('RECO_VIEW_REFRESH_FREQUENCY', '*')


@log_cron
@cron_context
@cron_require_feature(FeatureToggle.UPDATE_DISCOVERY_VIEW)
def update_discovery_view(app):
    DiscoveryView.refresh()
