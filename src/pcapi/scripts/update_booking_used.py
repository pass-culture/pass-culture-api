from datetime import datetime
from typing import List

from pcapi.core.bookings.models import Booking
import pcapi.core.bookings.repository as booking_repository
from pcapi.repository import repository
from pcapi.utils.logger import logger


def update_booking_used_after_stock_occurrence() -> None:
    bookings_to_process = booking_repository.find_not_used_and_not_cancelled()
    logger.info("processing %d bookings to update", len(bookings_to_process))
    bookings_to_update = []
    bookings_id_errors: List[Booking] = []

    for booking_index, booking in enumerate(bookings_to_process):
        if booking.stock.beginningDatetime:
            now = datetime.utcnow()
            if not booking.stock.isEventDeletable:
                booking.isUsed = True
                booking.dateUsed = now
                bookings_to_update.append(booking)

        if booking_index % 1000 == 0:
            logger.info("processing %d page", booking_index / 1000)
            logger.info("%d bookings to update", len(bookings_to_update))
            _save_bookings_to_update_in_db(bookings_to_update, bookings_id_errors)
            bookings_to_update = []

    _save_bookings_to_update_in_db(bookings_to_update, bookings_id_errors)

    if len(bookings_id_errors) > 0:
        logger.exception("Bookings id in error %s", bookings_id_errors)


def _save_bookings_to_update_in_db(bookings_to_update: List[Booking], bookings_id_errors: List[Booking]) -> None:
    try:
        repository.save(*bookings_to_update)
    except Exception:  # pylint: disable=broad-except
        bookings_id_errors.extend(bookings_to_update)
