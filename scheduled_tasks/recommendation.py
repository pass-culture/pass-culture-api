import os

from models import DiscoveryView
from scheduled_tasks.clock import app
from scheduled_tasks.decorators import log_cron

RECO_VIEW_REFRESH_FREQUENCY = os.environ.get('RECO_VIEW_REFRESH_FREQUENCY', '*')


@log_cron
def pc_update_recommendations_view():
    with app.app_context():
        DiscoveryView.refresh()
