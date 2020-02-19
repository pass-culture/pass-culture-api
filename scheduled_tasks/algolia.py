import os

from models.feature import FeatureToggle
from scheduled_tasks.decorators import log_cron, cron_context, cron_require_feature
from scripts.algolia_indexing.indexing import batch_deleting_expired_offers_in_algolia, \
    batch_indexing_offers_in_algolia_by_offer, batch_indexing_offers_in_algolia_by_venue, \
    batch_indexing_offers_in_algolia_by_venue_provider

ALGOLIA_CRON_INDEXING_OFFERS_BY_OFFER_FREQUENCY = os.environ.get(
    'ALGOLIA_CRON_INDEXING_OFFERS_BY_OFFER_FREQUENCY', '*')
ALGOLIA_CRON_INDEXING_OFFERS_BY_VENUE_FREQUENCY = os.environ.get(
    'ALGOLIA_CRON_INDEXING_OFFERS_BY_VENUE_FREQUENCY', '10')
ALGOLIA_CRON_INDEXING_OFFERS_BY_VENUE_PROVIDER_FREQUENCY = os.environ.get(
    'ALGOLIA_CRON_INDEXING_OFFERS_BY_VENUE_PROVIDER_FREQUENCY', '10')


@log_cron
@cron_context
@cron_require_feature(FeatureToggle.SYNCHRONIZE_ALGOLIA)
def index_offers_in_algolia_by_offer(app):
    batch_indexing_offers_in_algolia_by_offer(client=app.redis_client)


@log_cron
@cron_context
@cron_require_feature(FeatureToggle.SYNCHRONIZE_ALGOLIA)
def index_offers_in_algolia_by_venue(app):
    batch_indexing_offers_in_algolia_by_venue(client=app.redis_client)


@log_cron
@cron_context
@cron_require_feature(FeatureToggle.SYNCHRONIZE_ALGOLIA)
def index_offers_in_algolia_by_venue_provider(app):
    batch_indexing_offers_in_algolia_by_venue_provider(client=app.redis_client)


@log_cron
@cron_context
@cron_require_feature(FeatureToggle.SYNCHRONIZE_ALGOLIA)
def delete_expired_offers_in_algolia(app):
    batch_deleting_expired_offers_in_algolia(client=app.redis_client)
