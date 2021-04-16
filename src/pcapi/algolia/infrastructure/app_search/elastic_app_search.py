from typing import Dict
from typing import List

from elastic_enterprise_search import AppSearch

from pcapi.algolia.infrastructure.search_engine import SearchEngine
from pcapi.settings import APPSEARCH_API_KEY
from pcapi.settings import APPSEARCH_SERVER_URL


ENGINE_NAME = "passculture-testing"


class ElasticAppSearch(SearchEngine):
    def __init__(self) -> None:
        self.client = AppSearch(APPSEARCH_SERVER_URL, http_auth=APPSEARCH_API_KEY)

    def add_objects(self, objects: List[Dict]) -> None:
        # TODO (asaunier, 2021-04-13): We should handle query errors
        client = self.client.index_documents(engine_name=ENGINE_NAME, documents=objects)
        print(client)

    def delete_objects(self, object_ids: List[int]) -> None:
        self.client.delete_documents(engine_name=ENGINE_NAME, document_ids=object_ids)

    def clear_index(self) -> None:
        response = self.client.list_documents(engine_name=ENGINE_NAME)
        documents = response["results"]
        ids = [document["id"] for document in documents]

        if ids:
            self.delete_objects(ids)
