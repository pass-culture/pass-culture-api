from domain.types import get_formatted_event_or_thing_types_by_value
from models.pc_object import PcObject
from utils.logger import logger
from utils.test_utils import create_event_offer

def create_industrial_event_offers(
        events_by_name,
        venues_by_name,
        offerers_by_name
):
    logger.info('create_industrial_event_offers')

    types_by_value = get_formatted_event_or_thing_types_by_value()

    event_offers_by_name = {}

    for offerer in offerers_by_name.values():

        physical_venues = [
            venue for venue in offerer.managedVenues
            if not venue.isVirtual
        ]
        for physical_venue in physical_venues:

            virtual_venue = venues_by_name[physical_venue.name + " (Offre en ligne)"]

            for event in events_by_name.values():

                event_type = types_by_value[event.type]
                if event_type['offlineOnly']:
                    event_venue = physical_venue
                elif event_type['onlineOnly']:
                    event_venue = virtual_venue
                else:
                    event_venue = physical_venue

                name = "{} / {}".format(event.name, event_venue.name)
                event_offers_by_name[name] = create_event_offer(
                    event_venue,
                    event=event,
                    event_type=event.type
                )

    PcObject.check_and_save(*event_offers_by_name.values())

    logger.info('created {} event_offers'.format(len(event_offers_by_name)))

    return event_offers_by_name
