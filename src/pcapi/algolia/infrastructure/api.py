from typing import Dict
from typing import List

from pcapi.algolia.infrastructure.algolia.algolia import AlgoliaSearch
from pcapi.algolia.infrastructure.algolia.builder_algolia import build_algolia_object
from pcapi.core.offers.models import Offer


def build_object(offer: Offer) -> Dict:
    return build_algolia_object(offer)


def add_objects(objects: List[Dict]) -> None:
    AlgoliaSearch().add_objects(objects)


def delete_objects(object_ids: List[int]) -> None:
    AlgoliaSearch().delete_objects(object_ids)


def clear_index() -> None:
    AlgoliaSearch().clear_index()
