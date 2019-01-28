import random

from models.offer_type import EventType
from models.pc_object import PcObject
from utils.logger import logger
from utils.test_utils import create_booking

BOOKING_MODULO = 2
USED_BOOKING_MODULO = 2

def create_industrial_bookings(recommendations_by_name, stocks_by_name):
    logger.info('create_industrial_bookings')

    bookings_by_name = {}

    token = 100000

    stocks = stocks_by_name.values()

    reco_to_create_from = list(recommendations_by_name.items())[::BOOKING_MODULO]

    for (reco_index, (recommendation_name, recommendation)) in enumerate(reco_to_create_from):

        offer = recommendation.offer
        user = recommendation.user

        not_bookable_recommendation = offer is None
        if not_bookable_recommendation:
            continue

        user_has_no_booking = \
            user.firstName != "PC Test Jeune" or \
            "has-signed-up" in user.email

        if user_has_no_booking:
            continue

        user_has_only_activation_booked = \
            "has-booked-activation" in user.email or \
            "has-confirmed-activation" in user.email

        is_activation_offer = offer.eventOrThing.offerType['value'] == str(EventType.ACTIVATION)

        if user_has_only_activation_booked and not is_activation_offer:
            continue

        recommendation_stocks = [
            stock for stock in stocks
            if stock.offer == offer or\
            stock.eventOccurrence in offer.eventOccurrences
        ]

        stock = recommendation_stocks[0]

        booking_name = "{} / {}".format(recommendation_name, str(token))

        is_used = False
        if is_activation_offer:
            is_used = True if "has-confirmed-activation" in user.email or \
                              "has-booked-some" in user.email or \
                              "has-no-more-money" in user.email else False
        else:
            is_used = reco_index%BOOKING_MODULO == 0

        booking = create_booking(
            user,
            is_used=is_used,
            recommendation=recommendation,
            stock=stock,
            token=str(token),
            venue=recommendation.offer.venue
        )

        token += 1

        bookings_by_name[booking_name] = booking


    PcObject.check_and_save(*bookings_by_name.values())

    logger.info('created {} bookings'.format(len(bookings_by_name)))

    return bookings_by_name
