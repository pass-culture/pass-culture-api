from typing import Dict
from typing import List

from pcapi.algolia.infrastructure.algolia.algolia import _init_algolia_client


def add_objects(objects: List[Dict]) -> None:
    _init_algolia_client().save_objects(objects)


def delete_objects(object_ids: List[int]) -> None:
    _init_algolia_client().delete_objects(object_ids)


def clear_index() -> None:
    _init_algolia_client().clear_objects()
