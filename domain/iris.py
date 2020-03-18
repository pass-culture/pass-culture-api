from typing import Callable, Optional

from models import Venue
from repository.iris_venues_queries import find_ids_of_irises_located_near_venue, insert_venue_in_iris_venue, \
    get_iris_containing_user_location, get_iris_containing_user_postal_code


def _link_venue_to_irises(venue: Venue) -> None:
    if not venue.isVirtual:
        iris_ids_near_venue = find_ids_of_irises_located_near_venue(venue.id)
        insert_venue_in_iris_venue(venue.id, iris_ids_near_venue)


def link_valid_venue_to_irises(venue: Venue, link_venue_to_irises: Callable = _link_venue_to_irises) -> None:
    if venue.isValidated and venue.managingOfferer.isValidated:
        link_venue_to_irises(venue)


def get_iris_according_to_user_geolocation(latitude: Optional[int], longitude: Optional[int], user_postal_code: str) -> int:
    user_is_located = latitude and longitude
    iris_id = get_iris_containing_user_location(latitude, longitude) if user_is_located \
        else get_iris_containing_user_postal_code(user_postal_code)
    return iris_id
