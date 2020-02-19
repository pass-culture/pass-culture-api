from local_providers.provider_manager import synchronize_venue_providers_for_provider
from local_providers.venue_provider_worker import update_venues_for_specific_provider
from models.feature import FeatureToggle
from repository.provider_queries import get_provider_by_local_class
from scheduled_tasks.decorators import log_cron, cron_require_feature, cron_context

TITELIVE_STOCKS_PROVIDER_NAME = "TiteLiveStocks"
ALLOCINE_STOCKS_PROVIDER_NAME = "AllocineStocks"
LIBRAIRES_STOCKS_PROVIDER_NAME = "LibrairesStocks"


@log_cron
@cron_context
def pc_synchronize_allocine_stocks(app):
    allocine_stocks_provider_id = get_provider_by_local_class(ALLOCINE_STOCKS_PROVIDER_NAME).id
    synchronize_venue_providers_for_provider(allocine_stocks_provider_id)


@log_cron
@cron_context
@cron_require_feature(FeatureToggle.SYNCHRONIZE_LIBRAIRES)
def synchronize_libraires_stocks(app):
    libraires_stocks_provider_id = get_provider_by_local_class(LIBRAIRES_STOCKS_PROVIDER_NAME).id
    synchronize_venue_providers_for_provider(libraires_stocks_provider_id)


@log_cron
@cron_context
def pc_synchronize_titelive_stocks(app):
    titelive_stocks_provider_id = get_provider_by_local_class(TITELIVE_STOCKS_PROVIDER_NAME).id
    update_venues_for_specific_provider(titelive_stocks_provider_id)
