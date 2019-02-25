from models.pc_object import PcObject
from utils.logger import logger
from tests.test_utils import create_thing_offer

DEACTIVATED_OFFERS_PICK_MODULO = 3
THINGS_PER_OFFERER = 5

def create_industrial_thing_offers(
        things_by_name,
        offerers_by_name,
        venues_by_name
):
    logger.info('create_industrial_thing_offers')

    thing_offers_by_name = {}

    id_at_providers = 1234
    thing_index = 0
    offer_index = 0
    thing_items = list(things_by_name.items())

    for offerer in offerers_by_name.values():

        virtual_venue = [
            venue for venue in offerer.managedVenues
            if venue.isVirtual
        ][0]

        physical_venue_name = virtual_venue.name.replace(" (Offre en ligne)", "")
        physical_venue = venues_by_name.get(physical_venue_name)

        for venue_thing_index in range(0, THINGS_PER_OFFERER):

            thing_venue = None
            while thing_venue is None:
                rest_thing_index = (venue_thing_index + thing_index)%len(thing_items)

                (thing_name, thing) = thing_items[rest_thing_index]

                if thing.offerType['offlineOnly']:
                    thing_venue = physical_venue
                elif thing.offerType['onlineOnly']:
                    thing_venue = virtual_venue
                else:
                    thing_venue = physical_venue

                thing_index += 1

            name = "{} / {}".format(thing_name, thing_venue.name)
            if offer_index%DEACTIVATED_OFFERS_PICK_MODULO == 0:
                is_active = False
            else:
                is_active = True
            thing_offers_by_name[name] = create_thing_offer(
                thing_venue,
                thing=thing,
                thing_type=thing.type,
                is_active=is_active,
                id_at_providers=id_at_providers
            )
            offer_index += 1
            id_at_providers += 1

        thing_index += THINGS_PER_OFFERER

    PcObject.check_and_save(*thing_offers_by_name.values())

    logger.info('created {} thing_offers'.format(len(thing_offers_by_name)))

    return thing_offers_by_name
