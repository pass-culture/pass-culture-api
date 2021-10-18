import logging
import sys

from pcapi.core import search
from pcapi.repository import offer_queries


logger = logging.getLogger(__name__)


def batch_indexing_offers_in_algolia_from_database(
    ending_page: int = None, batch_size: int = 10000, starting_page: int = 0
) -> None:
    if not ending_page:
        ending_page = sys.maxsize

    for page in range(starting_page, ending_page):
        offer_ids = offer_queries.get_paginated_active_offer_ids(limit=batch_size, page=page)
        if not offer_ids:
            break
        search.reindex_offer_ids(offer_ids)
        logger.info("[ALGOLIA] Processed %d offers from page %d", len(offer_ids), page)
