from algoliasearch.search_client import SearchClient
from algoliasearch.search_index import SearchIndex

from pcapi import settings


def _init_algolia_client() -> SearchIndex:
    client = SearchClient.create(settings.ALGOLIA_APPLICATION_ID, settings.ALGOLIA_API_KEY)
    return client.init_index(settings.ALGOLIA_INDEX_NAME)
