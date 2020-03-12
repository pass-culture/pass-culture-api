from models import Venue
from repository.iris_venues_queries import find_ids_of_irises_located_near_venue, insert_venue_in_iris_venue


def link_venue_to_irises(venue: Venue) -> None:
    if not venue.isVirtual:
        iris_ids_near_venue = find_ids_of_irises_located_near_venue(venue.id)
        insert_venue_in_iris_venue(venue.id, iris_ids_near_venue)
