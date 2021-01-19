from typing import Callable
from typing import List

from pcapi.models.venue_type import VenueType


def get_types_of_venues(get_all_venue_types: Callable) -> List[VenueType]:
    return get_all_venue_types()
