from typing import List

from models import VenueProvider


def get_venue_providers_to_sync(provider_id: int) -> List[VenueProvider]:
    return VenueProvider.query \
        .filter(VenueProvider.providerId == provider_id) \
        .filter(VenueProvider.syncWorkerId == None) \
        .all()


def get_nb_containers_at_work() -> int:
    return VenueProvider.query \
        .filter(VenueProvider.syncWorkerId != None) \
        .count()
