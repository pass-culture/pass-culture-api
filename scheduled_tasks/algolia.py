import os

from scheduled_tasks.decorators import log_cron, cron_context
from scripts.algolia_indexing.indexing import batch_deleting_expired_offers_in_algolia

ALGOLIA_CRON_INDEXING_OFFERS_BY_OFFER_FREQUENCY = os.environ.get(
    'ALGOLIA_CRON_INDEXING_OFFERS_BY_OFFER_FREQUENCY', '*')
ALGOLIA_CRON_INDEXING_OFFERS_BY_VENUE_FREQUENCY = os.environ.get(
    'ALGOLIA_CRON_INDEXING_OFFERS_BY_VENUE_FREQUENCY', '10')
ALGOLIA_CRON_INDEXING_OFFERS_BY_VENUE_PROVIDER_FREQUENCY = os.environ.get(
    'ALGOLIA_CRON_INDEXING_OFFERS_BY_VENUE_PROVIDER_FREQUENCY', '10')


@log_cron
@cron_context
def index_offers_in_algolia_by_offer(app):
    index_offers_in_algolia_by_offer(client=app.redis_client)


@log_cron
@cron_context
def index_offers_in_algolia_by_venue(app):
    index_offers_in_algolia_by_venue(client=app.redis_client)


@log_cron
@cron_context
def index_offers_in_algolia_by_venue_provider(app):
    index_offers_in_algolia_by_venue_provider(client=app.redis_client)


@log_cron
@cron_context
def delete_expired_offers_in_algolia(app):
    batch_deleting_expired_offers_in_algolia(client=app.redis_client)
