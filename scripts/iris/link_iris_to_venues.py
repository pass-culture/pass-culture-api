from typing import List

from models import Venue, Offerer
from repository.iris_venues_queries import find_ids_of_irises_located_near_venue, insert_venue_in_iris_venue


def link_irises_to_existing_physical_venues(search_radius: int):
    venue_ids = _find_all_venue_ids_to_link()
    for venue_id in venue_ids:
        iris_ids = find_ids_of_irises_located_near_venue(venue_id, search_radius)
        insert_venue_in_iris_venue(venue_id, iris_ids)


def _find_all_venue_ids_to_link() -> List[int]:
    venues = Venue.query \
        .join(Offerer) \
        .filter(Venue.isVirtual == False) \
        .filter(Venue.validationToken == None) \
        .filter(Offerer.validationToken == None) \
        .with_entities(Venue.id) \
        .all()
    return [venue.id for venue in venues]
