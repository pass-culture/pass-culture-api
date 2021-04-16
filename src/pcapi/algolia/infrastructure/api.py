from typing import Dict
from typing import List

from pcapi.algolia.infrastructure.algolia.algolia import AlgoliaSearch
from pcapi.algolia.infrastructure.algolia.builder_algolia import build_algolia_object
from pcapi.algolia.infrastructure.app_search.builder_appsearch import build_appsearch_object
from pcapi.algolia.infrastructure.app_search.elastic_app_search import ElasticAppSearch
from pcapi.algolia.infrastructure.search_engine import SearchEngine
from pcapi.core.offers.models import Offer
from pcapi.settings import IS_ALGOLIA_REPLACED_BY_APPSEARCH


def _get_client() -> SearchEngine:
    if IS_ALGOLIA_REPLACED_BY_APPSEARCH:
        return ElasticAppSearch()

    return AlgoliaSearch()


def build_object(offer: Offer) -> Dict:
    if IS_ALGOLIA_REPLACED_BY_APPSEARCH:
        return build_appsearch_object(offer)

    return build_algolia_object(offer)


def add_objects(objects: List[Dict]) -> None:
    _get_client().add_objects(objects)


def delete_objects(object_ids: List[int]) -> None:
    _get_client().delete_objects(object_ids)


def clear_index() -> None:
    _get_client().clear_index()
