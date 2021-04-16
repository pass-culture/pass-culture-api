from typing import Dict
from typing import List

from algoliasearch.search_client import SearchClient

from pcapi import settings
from pcapi.algolia.infrastructure.search_engine import SearchEngine


class AlgoliaSearch(SearchEngine):
    def __init__(self):
        client = SearchClient.create(settings.ALGOLIA_APPLICATION_ID, settings.ALGOLIA_API_KEY)
        self.client = client.init_index(settings.ALGOLIA_INDEX_NAME)

    def add_objects(self, objects: List[Dict]) -> None:
        self.client.save_objects(objects)

    def delete_objects(self, object_ids: List[int]) -> None:
        self.client.delete_objects(object_ids)

    def clear_index(self) -> None:
        self.client.clear_objects()
