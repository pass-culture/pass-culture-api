from datetime import datetime, timedelta

from models import PcObject, Booking
from tests.conftest import clean_database, TestClient
from tests.test_utils import create_deposit, create_venue, create_offerer, \
    create_user, create_booking, create_offer_with_event_product, \
    create_event_occurrence, create_stock_from_event_occurrence
from utils.human_ids import humanize


class Patch:
    class Returns200:
        @clean_database
        def expect_the_booking_to_be_cancelled_by_current_user(self, app):
            # Given
            in_four_days = datetime.utcnow() + timedelta(days=4)
            in_five_days = datetime.utcnow() + timedelta(days=5)
            user = create_user(email='test@email.com')
            deposit_date = datetime.utcnow() - timedelta(minutes=2)
            deposit = create_deposit(user, deposit_date, amount=500)
            offerer = create_offerer()
            venue = create_venue(offerer)
            offer = create_offer_with_event_product(venue)
            event_occurrence = create_event_occurrence(offer, beginning_datetime=in_four_days,
                                                       end_datetime=in_five_days)
            stock = create_stock_from_event_occurrence(event_occurrence)
            booking = create_booking(user, stock, venue)
            PcObject.save(user, deposit, booking)
            booking_id = booking.id

            # When
            response = TestClient(app.test_client()).with_auth(user.email) \
                .patch('/bookings/' + humanize(booking.id), json={"isCancelled": True})

            # Then
            assert response.status_code == 200
            assert Booking.query.get(booking_id).isCancelled

        @clean_database
        def expect_the_booking_to_be_cancelled_by_admin_for_someone_else(self, app):
            # Given
            admin_user = create_user(email='test@email.com', can_book_free_offers=False, is_admin=True)
            other_user = create_user(email='test2@email.com')
            deposit_date = datetime.utcnow() - timedelta(minutes=2)
            deposit = create_deposit(other_user, deposit_date, amount=500)
            booking = create_booking(other_user)
            PcObject.save(admin_user, other_user, deposit, booking)
            booking_id = booking.id

            # When
            response = TestClient(app.test_client()).with_auth(admin_user.email) \
                .patch('/bookings/' + humanize(booking.id), json={"isCancelled": True})

            # Then
            assert response.status_code == 200
            assert Booking.query.get(booking_id).isCancelled

    class Returns400:
        @clean_database
        def when_the_booking_cannot_be_cancelled(self, app):
            # Given
            user = create_user(email='test@email.com')
            deposit_date = datetime.utcnow() - timedelta(minutes=2)
            deposit = create_deposit(user, deposit_date, amount=500)
            booking = create_booking(user, is_used=True)
            PcObject.save(user, deposit, booking)
            booking_id = booking.id

            # When
            response = TestClient(app.test_client()).with_auth(user.email) \
                .patch('/bookings/' + humanize(booking.id), json={"isCancelled": True})

            # Then
            assert response.status_code == 400
            assert response.json['booking'] == ["Impossible d\'annuler une réservation consommée"]
            assert not Booking.query.get(booking_id).isCancelled

        @clean_database
        def when_trying_to_patch_something_else_than_is_cancelled(self, app):
            # Given
            user = create_user(email='test@email.com')
            deposit_date = datetime.utcnow() - timedelta(minutes=2)
            deposit = create_deposit(user, deposit_date, amount=500)
            booking = create_booking(user, quantity=1)
            PcObject.save(user, deposit, booking)
            booking_id = booking.id

            # When
            response = TestClient(app.test_client()).with_auth(user.email) \
                .patch('/bookings/' + humanize(booking.id), json={"quantity": 3})

            # Then
            assert response.status_code == 400
            assert booking.quantity == 1

        @clean_database
        def when_trying_to_revert_cancellation(self, app):
            # Given
            user = create_user(email='test@email.com')
            deposit_date = datetime.utcnow() - timedelta(minutes=2)
            deposit = create_deposit(user, deposit_date, amount=500)
            booking = create_booking(user)
            booking.isCancelled = True
            PcObject.save(user, deposit, booking)
            booking_id = booking.id

            # When
            response = TestClient(app.test_client()).with_auth(user.email) \
                .patch('/bookings/' + humanize(booking.id), json={"isCancelled": False})

            # Then
            assert response.status_code == 400
            assert Booking.query.get(booking_id).isCancelled

        @clean_database
        def when_event_beginning_date_time_is_in_less_than_72_hours(self, app):
            # Given
            in_five_days = datetime.utcnow() + timedelta(days=5)
            in_one_days = datetime.utcnow() + timedelta(days=1)
            user = create_user(email='test@email.com')
            deposit_date = datetime.utcnow() - timedelta(minutes=2)
            deposit = create_deposit(user, deposit_date, amount=500)
            offerer = create_offerer()
            venue = create_venue(offerer)
            offer = create_offer_with_event_product(venue)
            event_occurrence = create_event_occurrence(offer, beginning_datetime=in_one_days, end_datetime=in_five_days)
            stock = create_stock_from_event_occurrence(event_occurrence)
            booking = create_booking(user, stock, venue)
            PcObject.save(user, deposit, booking)

            # When
            response = TestClient(app.test_client()).with_auth(user.email) \
                .patch('/bookings/' + humanize(booking.id), json={"isCancelled": True})

            # Then
            assert response.status_code == 400

    class Returns403:
        @clean_database
        def when_cancelling_a_booking_of_someone_else(self, app):
            # Given
            other_user = create_user(email='test2@email.com')
            deposit_date = datetime.utcnow() - timedelta(minutes=2)
            deposit = create_deposit(other_user, deposit_date, amount=500)
            booking = create_booking(other_user)
            user = create_user(email='test@email.com')
            PcObject.save(user, other_user, deposit, booking)
            booking_id = booking.id

            # When
            response = TestClient(app.test_client()).with_auth(user.email) \
                .patch('/bookings/' + humanize(booking.id), json={"isCancelled": True})

            # Then
            assert response.status_code == 403
            assert not Booking.query.get(booking_id).isCancelled

    class Returns404:
        @clean_database
        def when_the_booking_does_not_exist(self, app):
            # Given
            user = create_user(email='test@email.com')
            PcObject.save(user)

            # When
            response = TestClient(app.test_client()).with_auth(user.email) \
                .patch('/bookings/AX', json={"isCancelled": True})

            # Then
            assert response.status_code == 404
