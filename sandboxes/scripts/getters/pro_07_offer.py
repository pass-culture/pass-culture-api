from models import Offerer
from models import Offerer
from models.event import Event
from models.offer import Offer
from models.thing import Thing
from models.user import User
from models.venue import Venue
from repository.offerer_queries import keep_offerers_with_at_least_one_physical_venue
from repository.user_queries import filter_users_with_at_least_one_validated_offerer_validated_user_offerer
from sandboxes.scripts.utils.helpers import get_offer_helper, \
                                            get_offerer_helper, \
                                            get_user_helper, \
                                            get_venue_helper

def get_existing_pro_validated_user_with_at_least_one_visible_offer():
    query = User.query.filter(User.validationToken == None)
    query = filter_users_with_at_least_one_validated_offerer_validated_user_offerer(query)
    query = query.join(Venue, Venue.managingOffererId == Offerer.id).join(Offer)
    user = query.first()

    for uo in user.UserOfferers:
        if uo.validationToken == None and uo.offerer.validationToken == None:
            for venue in uo.offerer.managedVenues:
                if venue.offers:
                    offer = venue.offers[0]
                    return {
                        "offer": get_offer_helper(offer),
                        "user": get_user_helper(user)
                    }


def get_existing_pro_validated_user_with_validated_offerer_validated_user_offerer_with_physical_venue():
    query = User.query.filter(User.validationToken == None)
    query = filter_users_with_at_least_one_validated_offerer_validated_user_offerer(query)
    query = keep_offerers_with_at_least_one_physical_venue(query)
    user = query.first()

    for uo in user.UserOfferers:
        if uo.validationToken == None and uo.offerer.validationToken == None:
            for venue in uo.offerer.managedVenues:
                if not venue.isVirtual:
                    return {
                        "offerer": get_offerer_helper(uo.offerer),
                        "user": get_user_helper(user),
                        "venue": get_venue_helper(venue)
                    }


def get_existing_pro_validated_user_with_validated_offerer_validated_user_offerer_with_virtual_venue():
    query = User.query.filter(User.validationToken == None)
    query = filter_users_with_at_least_one_validated_offerer_validated_user_offerer(query)
    user = query.first()

    for uo in user.UserOfferers:
        if uo.validationToken == None and uo.offerer.validationToken == None:
            for venue in uo.offerer.managedVenues:
                if venue.isVirtual:
                    return {
                        "offerer": get_offerer_helper(uo.offerer),
                        "user": get_user_helper(user),
                        "venue": get_venue_helper(venue)
                    }


def get_existing_pro_validated_user_with_validated_offerer_validated_user_offerer_with_thing_offer():
    query = User.query.filter(User.validationToken == None)
    query = filter_users_with_at_least_one_validated_offerer_validated_user_offerer(query)
    query = query.join(Venue).join(Offer).filter(Offer.thingId != None)
    user = query.first()

    for uo in user.UserOfferers:
        if uo.validationToken == None and uo.offerer.validationToken == None:
            for venue in uo.offerer.managedVenues:
                for offer in venue.offers:
                    if isinstance(offer.eventOrThing, Thing):
                        return {
                            "offer": get_offer_helper(offer),
                            "offerer": get_offerer_helper(uo.offerer),
                            "user": get_user_helper(user),
                            "venue": get_venue_helper(venue)
                        }

def get_existing_pro_validated_user_with_validated_offerer_validated_user_offerer_with_event_offer():
    query = User.query.filter(User.validationToken == None)
    query = filter_users_with_at_least_one_validated_offerer_validated_user_offerer(query)
    query = query.join(Venue).join(Offer).filter(Offer.eventId != None)
    user = query.first()

    for uo in user.UserOfferers:
        if uo.validationToken == None and uo.offerer.validationToken == None:
            for venue in uo.offerer.managedVenues:
                for offer in venue.offers:
                    if isinstance(offer.eventOrThing, Event):
                        return {
                            "offer": get_offer_helper(offer),
                            "offerer": get_offerer_helper(uo.offerer),
                            "user": get_user_helper(user),
                            "venue": get_venue_helper(venue)
                        }
