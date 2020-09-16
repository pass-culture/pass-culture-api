import datetime

import domain.expenses
from models.booking_sql_entity import BookingSQLEntity
from models.stock_sql_entity import StockSQLEntity
from models.db import db

from . import exceptions


def check_can_book_free_offer(user, stock):
    if not user.canBookFreeOffers and stock.price == 0:
        raise exceptions.CannotBookFreeOffers()


def check_offer_already_booked(user, offer):
    """Raise ``OfferIsAlreadyBooked`` if the user already booked this offer."""
    if (
        db.query(
            BookingSQLEntity.query
            .filter_by(
                userId=user.id,
                isCancelled=False,
            )
            .join(StockSQLEntity)
            .filter_by(StockSQLEntity.offerId == offer.id)
        )
    ):
        raise exceptions.OfferIsAlreadyBooked()


def check_quantity(offer, quantity):
    """May raise QuantityIsInvalid, depending on ``offer.isDuo``."""
    if offer.isDuo and quantity not in (1, 2):
        raise exceptions.QuantityIsInvalid(
            "Vous devez réserver une place ou deux dans le cas d'une offre DUO."
        )

    if not offer.isDuo and quantity != 1:
        raise exceptions.QuantityIsInvalid(
            "Vous ne pouvez réserver qu'une place pour cette offre."
        )


def check_stock_is_bookable(stock):
    if (
        stock.hasBookingLimitDatetimePassed
        or stock.isEventExpired
        or stock.isSoftDeleted
        or not stock.offer.isActive
        or not stock.offer.venue.isValidated
        or not stock.offer.venue.managingOfferer.isActive
        or not stock.offer.venue.managingOfferer.isValidated
        or (stock.quantity is None and stock.remainingQuantity <= 0)
    ):
        raise exceptions.StockIsNotBookable()


def check_expenses_limits(expenses, requested_booking):
    """Raise an error if fulfilling the booking request would exceed the
    user's expense limits.
    """
    offer = requested_booking.stock.offer

    if (expenses['all']['actual'] + requested_booking.total_amount) > expenses['all']['max']:
        raise exceptions.UserHasInsufficientFunds()

    if domain.expenses.is_eligible_to_physical_offers_capping(offer):
        expected_total =  expenses['physical']['actual'] + requested_booking.total_amount
        if expected_total > expenses['physical']['max']:
            raise exceptions.PhysicalExpenseLimitHasBeenReached(expenses['physical']['max'])

    if domain.expenses.is_eligible_to_digital_offers_capping(offer):
        expected_total = expenses['digital']['actual'] + requested_booking.total_amount
        if expected_total > expenses['digital']['max']:
            raise exceptions.DigitalExpenseLimitHasBeenReached(expenses['digital']['max'])


def check_can_cancel_booking(user, booking):
    if booking.user_id != user.id:
        raise exceptions.BookingDoesntExist()
    if booking.isUsed:
        raise exceptions.BookingIsAlreadyUsed()
    if booking.stock.beginningDatetime is not None:
        if booking.stock.beginningDatetime < datetime.datetime.utcnow() + datetime.timedelta(hours=72):
            raise exceptions.EventHappensInLessThan72Hours()
