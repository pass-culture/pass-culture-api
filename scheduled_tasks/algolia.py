import os

from scheduled_tasks.decorators import log_cron
from scheduled_tasks.redis_clock import app
from scripts.algolia_indexing.indexing import batch_indexing_offers_in_algolia_by_offer, \
    batch_indexing_offers_in_algolia_by_venue, batch_indexing_offers_in_algolia_by_venue_provider, \
    batch_deleting_expired_offers_in_algolia

ALGOLIA_CRON_INDEXING_OFFERS_BY_OFFER_FREQUENCY = os.environ.get(
    'ALGOLIA_CRON_INDEXING_OFFERS_BY_OFFER_FREQUENCY', '*')
ALGOLIA_CRON_INDEXING_OFFERS_BY_VENUE_FREQUENCY = os.environ.get(
    'ALGOLIA_CRON_INDEXING_OFFERS_BY_VENUE_FREQUENCY', '10')
ALGOLIA_CRON_INDEXING_OFFERS_BY_VENUE_PROVIDER_FREQUENCY = os.environ.get(
    'ALGOLIA_CRON_INDEXING_OFFERS_BY_VENUE_PROVIDER_FREQUENCY', '10')


@log_cron
def pc_batch_indexing_offers_in_algolia_by_offer():
    with app.app_context():
        batch_indexing_offers_in_algolia_by_offer(client=app.redis_client)


@log_cron
def pc_batch_indexing_offers_in_algolia_by_venue():
    with app.app_context():
        batch_indexing_offers_in_algolia_by_venue(client=app.redis_client)


@log_cron
def pc_batch_indexing_offers_in_algolia_by_venue_provider():
    with app.app_context():
        batch_indexing_offers_in_algolia_by_venue_provider(client=app.redis_client)


@log_cron
def pc_batch_deleting_expired_offers_in_algolia():
    with app.app_context():
        batch_deleting_expired_offers_in_algolia(client=app.redis_client)
