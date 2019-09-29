from datetime import datetime
from freezegun import freeze_time
from sqlalchemy_api_handler import ApiHandler

from models import Booking
from scripts.update_booking_used import update_booking_used_after_stock_occurrence
from tests.conftest import clean_database
from tests.test_utils import create_deposit, create_booking, create_user, create_offerer, create_venue, \
    create_offer_with_event_product, create_stock, create_offer_with_thing_product


class UpdateBookingUsedTest:
    @clean_database
    def test_update_booking_used_when_booking_is_on_thing_product(self, app):
        # Given
        user = create_user()
        deposit = create_deposit(user)

        offerer = create_offerer()
        venue = create_venue(offerer)
        offer = create_offer_with_thing_product(venue)
        stock = create_stock(offer=offer,
                             beginning_datetime=None,
                             end_datetime=None)
        booking = create_booking(user, stock=stock, is_used=False)
        ApiHandler.save(user, deposit, booking, stock)

        # When
        update_booking_used_after_stock_occurrence()

        # Then
        updated_booking = Booking.query.first()
        assert not updated_booking.isUsed
        assert not updated_booking.dateUsed

    @freeze_time('2019-10-13')
    @clean_database
    def test_update_booking_used_when_event_date_is_3_days_before(self, app):
        # Given
        user = create_user()
        deposit = create_deposit(user)

        offerer = create_offerer()
        venue = create_venue(offerer)
        offer = create_offer_with_event_product(venue)
        stock = create_stock(offer=offer,
                             beginning_datetime=datetime(2019, 10, 9, 10, 20, 00),
                             end_datetime=datetime(2019, 10, 9, 12, 20, 0))
        booking = create_booking(user, stock=stock, is_used=False)
        ApiHandler.save(user, deposit, booking, stock)

        # When
        update_booking_used_after_stock_occurrence()

        # Then
        updated_booking = Booking.query.first()
        assert updated_booking.isUsed
        assert updated_booking.dateUsed == datetime(2019, 10, 13)

    @freeze_time('2019-10-10')
    @clean_database
    def test_update_booking_used_when_event_date_is_only_1_day_before(self, app):
        # Given
        user = create_user()
        deposit = create_deposit(user)

        offerer = create_offerer()
        venue = create_venue(offerer)
        offer = create_offer_with_event_product(venue)
        stock = create_stock(offer=offer,
                             beginning_datetime=datetime(2019, 10, 9, 10, 20, 00),
                             end_datetime=datetime(2019, 10, 9, 12, 20, 0))
        booking = create_booking(user, stock=stock, is_used=False)
        ApiHandler.save(user, deposit, booking, stock)

        # When
        update_booking_used_after_stock_occurrence()

        # Then
        updated_booking = Booking.query.first()
        assert not updated_booking.isUsed
        assert updated_booking.dateUsed is None

    @clean_database
    def test_does_not_update_booking_if_already_used(self, app):
        # Given
        user = create_user()
        deposit = create_deposit(user)

        offerer = create_offerer()
        venue = create_venue(offerer)
        offer = create_offer_with_event_product(venue)
        stock = create_stock(offer=offer,
                             beginning_datetime=datetime(2019, 10, 9, 10, 20, 00),
                             end_datetime=datetime(2019, 10, 9, 12, 20, 0))
        booking_date = datetime(2019, 10, 12, 12, 20, 0)
        booking = create_booking(user, stock=stock, is_used=True, date_used=booking_date)
        ApiHandler.save(user, deposit, booking, stock)

        # When
        update_booking_used_after_stock_occurrence()

        # Then
        updated_booking = Booking.query.first()
        assert updated_booking.isUsed
        assert updated_booking.dateUsed == booking_date
