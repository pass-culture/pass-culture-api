import logging

from pcapi.core import search
from pcapi.core.bookings import models as bookings_models
from pcapi.core.bookings import repository as bookings_repository
from pcapi.core.educational import repository as educational_repository
from pcapi.core.educational import validation
from pcapi.core.educational.exceptions import EducationalBookingNotFound
from pcapi.core.educational.models import EducationalBooking
from pcapi.core.offers import repository as offers_repository
from pcapi.repository import repository
from pcapi.repository import transaction


logger = logging.getLogger(__name__)

EAC_DEFAULT_BOOKED_QUANTITY = 1


def book_educational_offer(redactor_email: str, uai_code: str, stock_id: int) -> EducationalBooking:
    educational_institution = educational_repository.find_educational_institution_by_uai_code(uai_code)
    validation.check_institution_exists(educational_institution)

    # The call to transaction here ensures we free the FOR UPDATE lock
    # on the stock if validation issues an exception
    with transaction():
        stock = offers_repository.get_and_lock_stock(stock_id=stock_id)
        validation.check_stock_is_bookable(stock, EAC_DEFAULT_BOOKED_QUANTITY)

        educational_year = educational_repository.find_educational_year_by_date(stock.beginningDatetime)
        validation.check_educational_year_exists(educational_year)

        educational_booking = EducationalBooking(
            educationalInstitution=educational_institution,
            educationalYear=educational_year,
        )

        booking = bookings_models.Booking(
            educationalBooking=educational_booking,
            stockId=stock.id,
            amount=stock.price,
            token=bookings_repository.generate_booking_token(),
            venueId=stock.offer.venueId,
            offererId=stock.offer.venue.managingOffererId,
            status=bookings_models.BookingStatus.PENDING,
        )

        stock.dnBookedQuantity += EAC_DEFAULT_BOOKED_QUANTITY

        repository.save(booking)

    logger.info(
        "Redactor booked an educational offer",
        extra={
            "redactor": redactor_email,
            "offerId": stock.offerId,
            "stockId": stock.id,
            "bookingId": booking.id,
        },
    )

    search.async_index_offer_ids([stock.offerId])

    return booking


def confirm_educational_booking(educational_booking_id: int) -> EducationalBooking:
    educational_booking = educational_repository.find_educational_booking_by_id(educational_booking_id)
    if educational_booking is None:
        raise EducationalBookingNotFound()

    booking: bookings_models.Booking = educational_booking.booking
    if booking.status == bookings_models.BookingStatus.CONFIRMED:
        return booking

    educational_institution_id = educational_booking.educationalInstitutionId
    educational_year_id = educational_booking.educationalYearId
    with transaction():
        deposit = educational_repository.get_and_lock_educational_deposit(
            educational_institution_id, educational_year_id
        )
        validation.check_institution_fund(
            educational_institution_id,
            educational_year_id,
            booking.total_amount,
            deposit,
        )
        booking.mark_as_confirmed()
        repository.save(booking)

        return educational_booking
