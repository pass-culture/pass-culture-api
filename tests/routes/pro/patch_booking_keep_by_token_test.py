from decimal import Decimal

import pytest

from pcapi.core.bookings.factories import BookingFactory
from pcapi.core.offerers.factories import ApiKeyFactory
from pcapi.core.offerers.factories import DEFAULT_CLEAR_API_KEY
import pcapi.core.offers.factories as offers_factories
from pcapi.core.users.factories import UserFactory
from pcapi.model_creators.generic_creators import create_booking
from pcapi.model_creators.generic_creators import create_offerer
from pcapi.model_creators.generic_creators import create_payment
from pcapi.model_creators.generic_creators import create_user
from pcapi.model_creators.generic_creators import create_user_offerer
from pcapi.model_creators.generic_creators import create_venue
from pcapi.model_creators.specific_creators import create_event_occurrence
from pcapi.model_creators.specific_creators import create_offer_with_event_product
from pcapi.model_creators.specific_creators import create_stock_from_event_occurrence
from pcapi.model_creators.specific_creators import create_stock_with_event_offer
from pcapi.models import Booking
from pcapi.repository import repository
from pcapi.utils.token import random_token

from tests.conftest import TestClient


API_KEY_VALUE = random_token(64)


@pytest.mark.usefixtures("db_session")
class Returns204Test:
    class WithApiKeyAuthTest:
        def when_api_key_provided_is_related_to_regular_offer_with_rights(self, app):
            booking = BookingFactory(isUsed=True, token="ABCDEF")
            offerer = booking.stock.offer.venue.managingOfferer
            ApiKeyFactory(offerer=offerer)

            url = f"/v2/bookings/keep/token/{booking.token}"
            response = TestClient(app.test_client()).patch(
                url,
                headers={
                    "Authorization": f"Bearer {DEFAULT_CLEAR_API_KEY}",
                    "Origin": "http://localhost",
                },
            )

            assert response.status_code == 204
            booking = Booking.query.one()
            assert not booking.isUsed
            assert booking.dateUsed is None

        def expect_booking_to_be_used_with_non_standard_origin_header(self, app):
            booking = BookingFactory(isUsed=True, token="ABCDEF")
            offerer = booking.stock.offer.venue.managingOfferer
            ApiKeyFactory(offerer=offerer)

            url = f"/v2/bookings/keep/token/{booking.token}"
            response = TestClient(app.test_client()).patch(
                url,
                headers={
                    "Authorization": f"Bearer {DEFAULT_CLEAR_API_KEY}",
                    "Origin": "http://example.com",
                },
            )

            assert response.status_code == 204
            booking = Booking.query.one()
            assert not booking.isUsed
            assert booking.dateUsed is None

    class WithBasicAuthTest:
        def when_user_is_logged_in_and_regular_offer(self, app):
            booking = BookingFactory(isUsed=True, token="ABCDEF")
            pro_user = UserFactory(email="pro@example.com")
            offerer = booking.stock.offer.venue.managingOfferer
            offers_factories.UserOffererFactory(user=pro_user, offerer=offerer)

            url = f"/v2/bookings/keep/token/{booking.token}"
            response = TestClient(app.test_client()).with_auth("pro@example.com").patch(url)

            assert response.status_code == 204
            booking = Booking.query.one()
            assert not booking.isUsed
            assert booking.dateUsed is None

        def when_user_is_logged_in_expect_booking_with_token_in_lower_case_to_be_used(self, app):
            booking = BookingFactory(isUsed=True, token="ABCDEF")
            pro_user = UserFactory(email="pro@example.com")
            offerer = booking.stock.offer.venue.managingOfferer
            offers_factories.UserOffererFactory(user=pro_user, offerer=offerer)

            url = f"/v2/bookings/keep/token/{booking.token.lower()}"
            response = TestClient(app.test_client()).with_auth("pro@example.com").patch(url)

            assert response.status_code == 204
            booking = Booking.query.one()
            assert not booking.isUsed
            assert booking.dateUsed is None

        # FIXME: I don't understand what we're trying to test, here.
        def when_there_is_no_remaining_quantity_after_validating(self, app):
            booking = BookingFactory(
                isUsed=True,
                token="ABCDEF",
                stock__quantity=1,
            )
            pro_user = UserFactory(email="pro@example.com")
            offerer = booking.stock.offer.venue.managingOfferer
            offers_factories.UserOffererFactory(user=pro_user, offerer=offerer)

            url = f"/v2/bookings/keep/token/{booking.token.lower()}"
            response = TestClient(app.test_client()).with_auth("pro@example.com").patch(url)

            assert response.status_code == 204
            booking = Booking.query.one()
            assert not booking.isUsed
            assert booking.dateUsed is None


class Returns401Test:
    @pytest.mark.usefixtures("db_session")
    def when_user_not_logged_in_and_doesnt_give_api_key(self, app):
        # Given
        user = create_user(email="user@example.net")
        offerer = create_offerer()
        venue = create_venue(offerer)
        offer = create_offer_with_event_product(venue, event_name="Event Name")
        event_occurrence = create_event_occurrence(offer)
        stock = create_stock_from_event_occurrence(event_occurrence, price=0)
        booking = create_booking(user=user, stock=stock, venue=venue)

        repository.save(booking)

        # When
        url = "/v2/bookings/keep/token/{}".format(booking.token)
        response = TestClient(app.test_client()).patch(url)

        # Then
        assert response.status_code == 401

    @pytest.mark.usefixtures("db_session")
    def when_user_not_logged_in_and_given_api_key_that_does_not_exists(self, app):
        # Given
        user = create_user(email="user@example.net")
        offerer = create_offerer()
        venue = create_venue(offerer)
        offer = create_offer_with_event_product(venue, event_name="Event Name")
        event_occurrence = create_event_occurrence(offer)
        stock = create_stock_from_event_occurrence(event_occurrence, price=0)
        booking = create_booking(user=user, stock=stock, venue=venue)

        repository.save(booking)

        # When
        wrong_api_key = "Bearer WrongApiKey1234567"
        url = "/v2/bookings/keep/token/{}".format(booking.token)
        response = TestClient(app.test_client()).patch(
            url, headers={"Authorization": wrong_api_key, "Origin": "http://localhost"}
        )

        # Then
        assert response.status_code == 401


class Returns403Test:
    class WithApiKeyAuthTest:
        @pytest.mark.usefixtures("db_session")
        def when_the_api_key_is_not_linked_to_the_right_offerer(self, app):
            # Given
            user = create_user(email="user@example.net")
            pro_user = create_user(email="pro@example.net")
            offerer = create_offerer()
            offerer2 = create_offerer(siren="987654321")
            user_offerer = create_user_offerer(pro_user, offerer)
            venue = create_venue(offerer)
            offer = create_offer_with_event_product(venue, event_name="Event Name")
            event_occurrence = create_event_occurrence(offer)
            stock = create_stock_from_event_occurrence(event_occurrence, price=0)
            booking = create_booking(user=user, stock=stock, venue=venue)

            repository.save(pro_user, booking, user_offerer, offerer2)

            ApiKeyFactory(offerer=offerer2)

            # When
            user2_api_key = f"Bearer {DEFAULT_CLEAR_API_KEY}"
            url = "/v2/bookings/keep/token/{}".format(booking.token)

            response = TestClient(app.test_client()).patch(
                url, headers={"Authorization": user2_api_key, "Origin": "http://localhost"}
            )

            # Then
            assert response.status_code == 403
            assert response.json["user"] == ["Vous n'avez pas les droits suffisants pour valider cette contremarque."]

        @pytest.mark.usefixtures("db_session")
        def when_api_key_is_provided_and_booking_has_been_cancelled_already(self, app):
            # Given
            user = create_user()
            pro_user = create_user(email="pro@example.net")
            offerer = create_offerer()
            user_offerer = create_user_offerer(pro_user, offerer)
            venue = create_venue(offerer)
            stock = create_stock_with_event_offer(offerer, venue, price=0)
            booking = create_booking(user=user, stock=stock, is_used=True, venue=venue, is_cancelled=True)
            repository.save(booking, user_offerer)
            ApiKeyFactory(offerer=offerer)
            url = f"/v2/bookings/keep/token/{booking.token}"
            user2_api_key = f"Bearer {DEFAULT_CLEAR_API_KEY}"

            # When
            response = TestClient(app.test_client()).patch(
                url, headers={"Authorization": user2_api_key, "Origin": "http://localhost"}
            )

            # Then
            assert response.status_code == 403
            assert response.json["booking"] == ["Cette réservation a été annulée"]
            assert Booking.query.get(booking.id).isUsed is True

    class WithBasicAuthTest:
        @pytest.mark.usefixtures("db_session")
        def when_user_is_not_attached_to_linked_offerer(self, app):
            # Given
            user = create_user()
            pro_user = create_user(email="pro@example.net")
            offerer = create_offerer()
            venue = create_venue(offerer)
            stock = create_stock_with_event_offer(offerer, venue, price=0)

            booking = create_booking(user=user, stock=stock, venue=venue)
            repository.save(booking, pro_user)

            # When
            url = "/v2/bookings/keep/token/{}?email={}".format(booking.token, user.email)
            response = TestClient(app.test_client()).with_auth("pro@example.net").patch(url)

            # Then
            assert response.status_code == 403
            assert response.json["user"] == ["Vous n'avez pas les droits suffisants pour valider cette contremarque."]
            assert Booking.query.get(booking.id).isUsed is False

        @pytest.mark.usefixtures("db_session")
        def when_user_is_logged_in_and_booking_has_been_cancelled_already(self, app):
            # Given
            admin = UserFactory(isAdmin=True)
            booking = BookingFactory(isCancelled=True, isUsed=True)
            url = f"/v2/bookings/keep/token/{booking.token}"

            # When
            response = TestClient(app.test_client()).with_auth(admin.email).patch(url)

            # Then
            assert response.status_code == 403
            assert response.json["booking"] == ["Cette réservation a été annulée"]
            assert Booking.query.get(booking.id).isUsed is True


class Returns404Test:
    class WithApiKeyAuthTest:
        @pytest.mark.usefixtures("db_session")
        def when_booking_is_not_provided_at_all(self, app):
            # When
            url = "/v2/bookings/keep/token/"
            user2_api_key = f"Bearer {DEFAULT_CLEAR_API_KEY}"

            response = TestClient(app.test_client()).patch(
                url, headers={"Authorization": user2_api_key, "Origin": "http://localhost"}
            )

            # Then
            assert response.status_code == 404

        @pytest.mark.usefixtures("db_session")
        def when_api_key_is_provided_and_booking_does_not_exist(self, app):
            # Given
            user = create_user()
            offerer = create_offerer()
            venue = create_venue(offerer)
            stock = create_stock_with_event_offer(offerer, venue, price=0)

            booking = create_booking(user=user, stock=stock, venue=venue)
            repository.save(booking)

            ApiKeyFactory(offerer=offerer)

            # When
            url = "/v2/bookings/keep/token/{}".format("456789")
            user2_api_key = f"Bearer {DEFAULT_CLEAR_API_KEY}"

            response = TestClient(app.test_client()).patch(
                url, headers={"Authorization": user2_api_key, "Origin": "http://localhost"}
            )

            # Then
            assert response.status_code == 404
            assert response.json["global"] == ["Cette contremarque n'a pas été trouvée"]

    class WithBasicAuthTest:
        @pytest.mark.usefixtures("db_session")
        def when_user_is_logged_in_and_booking_does_not_exist(self, app):
            # Given
            user = create_user()
            pro_user = create_user(email="pro@example.net")
            offerer = create_offerer()
            user_offerer = create_user_offerer(pro_user, offerer)
            venue = create_venue(offerer)
            stock = create_stock_with_event_offer(offerer, venue, price=0)

            booking = create_booking(user=user, stock=stock, venue=venue)
            repository.save(booking, user_offerer)

            # When
            url = "/v2/bookings/keep/token/{}".format("123456")
            response = TestClient(app.test_client()).with_auth("pro@example.net").patch(url)

            # Then
            assert response.status_code == 404
            assert response.json["global"] == ["Cette contremarque n'a pas été trouvée"]

        @pytest.mark.usefixtures("db_session")
        def when_user_is_logged_in_and_booking_token_is_null(self, app):
            # Given
            user = create_user()
            pro_user = create_user(email="pro@example.net")
            offerer = create_offerer()
            user_offerer = create_user_offerer(pro_user, offerer)
            venue = create_venue(offerer)
            stock = create_stock_with_event_offer(offerer, venue, price=0)

            booking = create_booking(user=user, stock=stock, venue=venue)

            repository.save(booking, user_offerer)

            # When
            url = "/v2/bookings/keep/token/"
            response = TestClient(app.test_client()).with_auth("pro@example.net").patch(url)

            # Then
            assert response.status_code == 404


class Returns410Test:
    class WithBasicAuthTest:
        @pytest.mark.usefixtures("db_session")
        def when_user_is_logged_in_and_booking_has_not_been_validated_already(self, app):
            # Given
            user = create_user()
            pro_user = create_user(email="pro@example.net")
            offerer = create_offerer()
            user_offerer = create_user_offerer(pro_user, offerer)
            venue = create_venue(offerer)
            stock = create_stock_with_event_offer(offerer, venue, price=0)

            booking = create_booking(user=user, stock=stock, venue=venue)
            repository.save(booking, user_offerer)

            # When
            url = "/v2/bookings/keep/token/{}".format(booking.token)
            response = TestClient(app.test_client()).with_auth("pro@example.net").patch(url)

            # Then
            assert response.status_code == 410
            assert response.json["booking"] == ["Cette réservation n'a pas encore été validée"]
            assert Booking.query.get(booking.id).isUsed is False

        @pytest.mark.usefixtures("db_session")
        def when_user_is_logged_in_and_booking_payment_exists(self, app):
            # Given
            user = create_user()
            pro_user = create_user(email="pro@example.net")
            offerer = create_offerer()
            user_offerer = create_user_offerer(pro_user, offerer)
            venue = create_venue(offerer)
            stock = create_stock_with_event_offer(offerer, venue, price=0)

            booking = create_booking(user=user, stock=stock, venue=venue, is_used=True)
            payment = create_payment(booking, offerer, Decimal(10), iban="CF13QSDFGH456789", bic="QSDFGH8Z555")

            repository.save(booking, user_offerer, payment)

            # When
            url = "/v2/bookings/keep/token/{}".format(booking.token)
            response = TestClient(app.test_client()).with_auth("pro@example.net").patch(url)

            # Then
            assert response.status_code == 410
            assert response.json["payment"] == ["Le remboursement est en cours de traitement"]
            assert Booking.query.get(booking.id).isUsed is True

    class WithApiKeyAuthTest:
        @pytest.mark.usefixtures("db_session")
        def when_api_key_is_provided_and_booking_has_not_been_validated_already(self, app):
            # Given
            user = create_user()
            pro_user = create_user(email="pro@example.net")
            offerer = create_offerer()
            user_offerer = create_user_offerer(pro_user, offerer)
            venue = create_venue(offerer)
            stock = create_stock_with_event_offer(offerer, venue, price=0)
            booking = create_booking(user=user, stock=stock, venue=venue)
            repository.save(booking, user_offerer)

            ApiKeyFactory(offerer=offerer)

            # When
            url = "/v2/bookings/keep/token/{}".format(booking.token)
            user2_api_key = f"Bearer {DEFAULT_CLEAR_API_KEY}"

            response = TestClient(app.test_client()).patch(
                url, headers={"Authorization": user2_api_key, "Origin": "http://localhost"}
            )
            # Then
            assert response.status_code == 410
            assert response.json["booking"] == ["Cette réservation n'a pas encore été validée"]
            assert Booking.query.get(booking.id).isUsed is False

        @pytest.mark.usefixtures("db_session")
        def when_api_key_is_provided_and_booking_payment_exists(self, app):
            # Given
            user = create_user()
            pro_user = create_user(email="pro@example.net")
            offerer = create_offerer()
            user_offerer = create_user_offerer(pro_user, offerer)
            venue = create_venue(offerer)
            stock = create_stock_with_event_offer(offerer, venue, price=0)

            booking = create_booking(user=user, stock=stock, venue=venue, is_used=True)
            payment = create_payment(booking, offerer, Decimal(10), iban="CF13QSDFGH456789", bic="QSDFGH8Z555")

            repository.save(booking, user_offerer, payment)

            ApiKeyFactory(offerer=offerer)

            # When
            url = "/v2/bookings/keep/token/{}".format(booking.token)
            user2_api_key = f"Bearer {DEFAULT_CLEAR_API_KEY}"

            response = TestClient(app.test_client()).patch(
                url, headers={"Authorization": user2_api_key, "Origin": "http://localhost"}
            )
            # Then
            assert response.status_code == 410
            assert response.json["payment"] == ["Le remboursement est en cours de traitement"]
            assert Booking.query.get(booking.id).isUsed is True
