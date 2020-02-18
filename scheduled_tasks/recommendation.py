import os

from models import DiscoveryView
from repository.recommendation_queries import delete_useless_recommendations
from scheduled_tasks.clock import app
from scheduled_tasks.decorators import log_cron


@log_cron
def pc_delete_useless_recommendations():
    with app.app_context():
        delete_useless_recommendations()


@log_cron
def pc_update_recommendations_view():
    with app.app_context():
        DiscoveryView.refresh()


RECO_VIEW_REFRESH_FREQUENCY = os.environ.get('RECO_VIEW_REFRESH_FREQUENCY', '*')
