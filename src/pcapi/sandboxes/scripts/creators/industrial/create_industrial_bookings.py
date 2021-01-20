from datetime import datetime

from pcapi.core.bookings.factories import BookingFactory
from pcapi.core.users.models import ExpenseDomain
from pcapi.core.users.models import User
from pcapi.model_creators.generic_creators import create_booking
from pcapi.models.offer_type import EventType
from pcapi.repository import repository
from pcapi.utils.logger import logger


MAX_RATIO_OF_EXPENSES = 0.8
OFFER_WITH_BOOKINGS_RATIO = 3
OFFER_WITH_SEVERAL_STOCKS_REMOVE_MODULO = 2
BOOKINGS_USED_REMOVE_MODULO = 5


def create_industrial_bookings(offers_by_name, users_by_name):
    logger.info("create_industrial_bookings")

    bookings_by_name = {}

    list_of_users_with_no_more_money = []

    token = 100000

    for (user_name, user) in users_by_name.items():
        if (
            user.firstName != "PC Test Jeune"
            or "has-signed-up" in user_name
            or "has-filled-cultural-survey" in user_name
        ):
            continue

        if "has-booked-some" in user.email:
            _create_has_booked_some_bookings(bookings_by_name, offers_by_name, user, user_name)
        else:
            token = _create_bookings_for_other_beneficiaries(
                bookings_by_name, list_of_users_with_no_more_money, offers_by_name, token, user, user_name
            )

    repository.save(*bookings_by_name.values())

    logger.info("created %d bookings", len(bookings_by_name))


def _create_bookings_for_other_beneficiaries(
    bookings_by_name, list_of_users_with_no_more_money, offers_by_name, token: int, user: User, user_name: str
) -> int:
    user_should_have_no_more_money = "has-no-more-money" in user.email
    for (offer_index, (offer_name, offer)) in enumerate(list(offers_by_name.items())):
        # FIXME (viconnex, 2020-12-22) trying to adapt previous code - not sure of the result and intention
        if offer_index % OFFER_WITH_BOOKINGS_RATIO != 0:
            continue

        if not offer.venue.managingOfferer.isValidated:
            continue

        user_has_only_activation_booked = (
            "has-booked-activation" in user.email or "has-confirmed-activation" in user.email
        )

        is_activation_offer = offer.product.offerType["value"] == str(EventType.ACTIVATION)

        if user_has_only_activation_booked and not is_activation_offer:
            continue

        for (index, stock) in enumerate(offer.stocks):
            # every STOCK_MODULO RECO will have several stocks
            if index > 0 and offer_index % (OFFER_WITH_SEVERAL_STOCKS_REMOVE_MODULO + index):
                continue

            booking_name = "{} / {} / {}".format(offer_name, user_name, str(token))

            is_used = False
            if is_activation_offer:
                is_used = (
                    "has-confirmed-activation" in user.email
                    or "has-booked-some" in user.email
                    or "has-no-more-money" in user.email
                )
            else:
                is_used = offer_index % BOOKINGS_USED_REMOVE_MODULO != 0

            if user_should_have_no_more_money and user not in list_of_users_with_no_more_money:
                booking_amount = user.deposits[0].amount
                list_of_users_with_no_more_money.append(user)
            elif user_should_have_no_more_money and user in list_of_users_with_no_more_money:
                booking_amount = 0
            else:
                booking_amount = None

            bookings_by_name[booking_name] = create_booking(
                user=user,
                amount=booking_amount,
                is_used=is_used,
                stock=stock,
                token=str(token),
                venue=offer.venue,
            )

            token = token + 1

            if bookings_by_name[booking_name].isUsed:
                bookings_by_name[booking_name].dateUsed = datetime.now()

    return token


def _create_has_booked_some_bookings(bookings_by_name, offers_by_name, user, user_name):

    for (offer_index, (offer_name, offer)) in enumerate(list(offers_by_name.items())):
        # FIXME (viconnex, 2020-12-22) trying to adapt previous code - not sure of the result and intention
        if offer_index % OFFER_WITH_BOOKINGS_RATIO != 0:
            continue

        # FIXME (asaunier, 2021-01-20): We should exclude non validated venues earlier
        if not offer.venue.managingOfferer.isValidated:
            continue

        digital_expenses = next(expense for expense in user.expenses if expense.domain == ExpenseDomain.DIGITAL)

        if digital_expenses.current > MAX_RATIO_OF_EXPENSES * float(digital_expenses.limit):
            break

        is_activation_offer = offer.product.offerType["value"] == str(EventType.ACTIVATION)

        for (index, stock) in enumerate(offer.stocks):
            # every STOCK_MODULO RECO will have several stocks
            if index > 0 and offer_index % (OFFER_WITH_SEVERAL_STOCKS_REMOVE_MODULO + index):
                continue

            is_used = False
            if is_activation_offer:
                is_used = True
            else:
                is_used = offer_index % BOOKINGS_USED_REMOVE_MODULO != 0

            booking = BookingFactory(user=user, isUsed=is_used, stock=stock)
            booking_name = "{} / {} / {}".format(offer_name, user_name, booking.token)
            bookings_by_name[booking_name] = booking

            if bookings_by_name[booking_name].isUsed:
                bookings_by_name[booking_name].dateUsed = datetime.now()
