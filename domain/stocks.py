from datetime import datetime, timedelta
from typing import List

from models import Booking, Stock

BOOKING_CANCELLATION_DELAY = timedelta(hours=72)
STOCK_DELETION_DELAY = timedelta(hours=48)


def delete_stock_and_cancel_bookings(stock: Stock) -> List[Booking]:
    if _is_thing(stock):
        stock.isSoftDeleted = True
        _cancel_unused_bookings(stock)
        return stock.bookings

    two_days_after_it_ends = stock.endDatetime + STOCK_DELETION_DELAY
    three_days_before_it_starts = stock.beginningDatetime - BOOKING_CANCELLATION_DELAY
    now = datetime.utcnow()

    if now <= three_days_before_it_starts:
        stock.isSoftDeleted = True
        _cancel_unused_bookings(stock)
    elif three_days_before_it_starts < now <= two_days_after_it_ends:
        stock.isSoftDeleted = True
        _cancel_all_bookings(stock)
    else:
        raise TooLateToDeleteError()

    return stock.bookings


class TooLateToDeleteError(Exception):
    def __init__(self):
        self.message = "L'événement s'est terminé il y a plus de deux jours, " \
                       "la suppression est impossible."


def _is_thing(stock: Stock) -> bool:
    return stock.beginningDatetime is None


def _cancel_unused_bookings(stock: Stock):
    for b in stock.bookings:
        if not b.isUsed:
            b.isCancelled = True


def _cancel_all_bookings(stock: Stock):
    for b in stock.bookings:
        b.isCancelled = True
