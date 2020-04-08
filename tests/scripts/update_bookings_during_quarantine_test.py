from _decimal import Decimal
from datetime import datetime, timedelta

from domain.payments import create_payment_for_booking
from domain.reimbursement import BookingReimbursement, ReimbursementRules
from scripts.cancel_bookings_during_quarantine import cancel_booking_status_for_events_happening_during_quarantine
from tests.conftest import clean_database
from models import Booking
from repository import repository
from tests.model_creators.generic_creators import create_user, create_stock, create_booking, create_venue, \
    create_offerer
from tests.model_creators.specific_creators import create_offer_with_event_product


class UpdateBookingDuringQuarantineTest:
    @clean_database
    def test_should_update_booking_if_happening_during_quarantine(self, app):
        # Given
        offerer = create_offerer()
        user = create_user()
        venue = create_venue(offerer)
        offer = create_offer_with_event_product(venue=venue)
        stock = create_stock(
            offer=offer, price=0,
            beginning_datetime=datetime(2020, 3, 18, 0, 0, 0)
        )
        yesterday = datetime.utcnow() - timedelta(days=1)
        booking = create_booking(
            user=user,
            stock=stock,
            token='AZERTY',
            is_used=True,
            date_used=yesterday
        )
        repository.save(booking)

        # When
        cancel_booking_status_for_events_happening_during_quarantine()

        # Then
        booking = Booking.query.one()
        assert booking.isUsed is False
        assert booking.dateUsed is None

    @clean_database
    def test_should_not_update_booking_if_not_happening_during_quarantine(self, app):
        # Given
        offerer = create_offerer()
        user = create_user()
        venue = create_venue(offerer)
        offer = create_offer_with_event_product(venue=venue)
        stock = create_stock(
            offer=offer, price=0,
            beginning_datetime=datetime(2019, 3, 12, 00, 00, 00)
        )
        date_used = datetime(2019, 3, 12, 00, 00, 00)
        booking = create_booking(
            user=user,
            stock=stock,
            token='AZERTY',
            is_used=True,
            date_used=date_used
        )
        repository.save(booking)

        # When
        cancel_booking_status_for_events_happening_during_quarantine()

        # Then
        booking = Booking.query.one()
        assert booking.isUsed is True
        assert booking.dateUsed == date_used

    @clean_database
    def test_should_not_update_booking_if_a_payment_has_been_made(self, app):
        # Given
        offerer = create_offerer()
        user = create_user()
        venue = create_venue(offerer)
        offer = create_offer_with_event_product(venue=venue)
        stock = create_stock(
            offer=offer, price=0,
            beginning_datetime=datetime(2019, 3, 12, 00, 00, 00)
        )
        date_used = datetime(2019, 3, 12, 00, 00, 00)
        booking = create_booking(
            user=user,
            stock=stock,
            token='QSDFG',
            is_used=True,
            date_used=date_used
        )
        booking_reimbursement = BookingReimbursement(
            booking,
            ReimbursementRules.PHYSICAL_OFFERS,
            Decimal(10))
        payment = create_payment_for_booking(booking_reimbursement)
        repository.save(booking, payment)

        # When
        cancel_booking_status_for_events_happening_during_quarantine()

        # Then
        bookings = Booking.query.all()

        assert bookings[0].isUsed is True
        assert bookings[0].dateUsed == date_used
