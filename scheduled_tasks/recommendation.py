import os

from models import DiscoveryView
from scheduled_tasks.decorators import log_cron, cron_context

RECO_VIEW_REFRESH_FREQUENCY = os.environ.get('RECO_VIEW_REFRESH_FREQUENCY', '*')


@log_cron
@cron_context
def update_recommendations_view(app):
    DiscoveryView.refresh()
