from datetime import datetime
from sqlalchemy_api_handler import ApiHandler

from domain.stocks import STOCK_DELETION_DELAY
from repository.booking_queries import find_all_not_used_and_not_cancelled


def update_booking_used_after_stock_occurrence():
    bookings_to_process = find_all_not_used_and_not_cancelled()
    bookings_id_errors = []

    for booking in bookings_to_process:
        if booking.stock.endDatetime:
            now = datetime.utcnow()
            booking_on_event_considered_used_after_delay = now > booking.stock.endDatetime + STOCK_DELETION_DELAY
            if booking_on_event_considered_used_after_delay:
                booking.isUsed = True
                booking.dateUsed = now
                try:
                    ApiHandler.save(booking)
                except Exception:
                    bookings_id_errors.append(booking.id)

    print("Bookings id in error %s" % bookings_id_errors)
