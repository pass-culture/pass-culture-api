from models import Event, Offer, Thing, Venue
from models.pc_object import PcObject
from utils.human_ids import dehumanize
from utils.logger import logger

def create_or_find_offer(offer_mock):
    if 'eventId' in offer_mock:
        event_or_thing = Event.query.get(dehumanize(offer_mock['eventId']))
        is_event = True
        query = Offer.query.filter_by(eventId=event_or_thing.id)
    else:
        event_or_thing = Thing.query.get(dehumanize(offer_mock['thingId']))
        is_event = False
        query = Offer.query.filter_by(thingId=event_or_thing.id)
    venue = Venue.query.get(dehumanize(offer_mock['venueId']))

    logger.info("look offer " + event_or_thing.name + " " + venue.name + " " + offer_mock.get('id'))

    if 'id' in offer_mock:
        offer = Offer.query.get(dehumanize(offer_mock['id']))
    else:
        offer = query.filter_by(venueId=venue.id).first()

    if offer is None:
        offer = Offer(from_dict=offer_mock)
        if is_event:
            offer.event = event_or_thing
        else:
            offer.thing = event_or_thing
        offer.venue = venue
        if 'id' in offer_mock:
            offer.id = dehumanize(offer_mock['id'])
        PcObject.check_and_save(offer)
        logger.info("created offer " + str(offer))
    else:
        logger.info('--already here-- offer' + str(offer))

    return offer
