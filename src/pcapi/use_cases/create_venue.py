from typing import Callable
from typing import Dict

from pcapi.domain.iris import link_valid_venue_to_irises
from pcapi.models.venue_sql_entity import VenueSQLEntity


def create_venue(venue_properties: Dict, save: Callable) -> VenueSQLEntity:
    venue = VenueSQLEntity(from_dict=venue_properties)

    save(venue)

    link_valid_venue_to_irises(venue=venue)

    return venue
