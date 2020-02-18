from local_providers.provider_manager import synchronize_venue_providers_for_provider
from local_providers.venue_provider_worker import update_venues_for_specific_provider
from models.feature import FeatureToggle
from repository.provider_queries import get_provider_by_local_class
from scheduled_tasks.clock import app
from scheduled_tasks.decorators import log_cron, cron_require_feature

TITELIVE_STOCKS_PROVIDER_NAME = "TiteLiveStocks"
ALLOCINE_STOCKS_PROVIDER_NAME = "AllocineStocks"
LIBRAIRIES_STOCKS_PROVIDER_NAME = "LibrairesStocks"


@log_cron
def pc_synchronize_allocine_stocks():
    with app.app_context():
        allocine_stocks_provider_id = get_provider_by_local_class(ALLOCINE_STOCKS_PROVIDER_NAME).id
        synchronize_venue_providers_for_provider(allocine_stocks_provider_id)


@log_cron
@cron_require_feature(FeatureToggle.SYNCRONIZE_LIBRAIRIES)
def synchronize_libraire_stocks():
    with app.app_context():
        librairies_stocks_provider_id = get_provider_by_local_class(LIBRAIRIES_STOCKS_PROVIDER_NAME).id
        synchronize_venue_providers_for_provider(librairies_stocks_provider_id)


@log_cron
def pc_synchronize_titelive_stocks():
    with app.app_context():
        with app.app_context():
            titelive_stocks_provider_id = get_provider_by_local_class(TITELIVE_STOCKS_PROVIDER_NAME).id
            update_venues_for_specific_provider(titelive_stocks_provider_id)
