from datetime import datetime
from decimal import Decimal


from models import PcObject, EventType, Booking, Stock
from tests.conftest import clean_database, TestClient
from tests.test_utils import create_venue, create_offerer, \
    create_user, create_booking, create_offer_with_event_product, \
    create_event_occurrence, create_stock_from_event_occurrence, create_user_offerer, create_payment
from tests.test_utils import create_api_key, create_stock_with_event_offer
from utils.token import random_token

API_KEY_VALUE = random_token(64)


class Patch:
    class Returns204:
        class WithApiKeyAuthTest:
            @clean_database
            def when_api_key_is_provided_and_rights_and_regular_offer(self, app):
                # Given
                user = create_user()
                offerer = create_offerer()
                venue = create_venue(offerer)
                stock = create_stock_with_event_offer(offerer, venue, price=0)

                booking = create_booking(user, stock, venue=venue, is_used=True)
                PcObject.save(booking, offerer)

                offererApiKey = create_api_key(offerer, API_KEY_VALUE)

                PcObject.save(offererApiKey)

                booking_id = booking.id

                # When
                user2_api_key = 'Bearer ' + offererApiKey.value
                url = '/v2/bookings/keep/token/{}'.format(booking.token)

                response = TestClient(app.test_client()).patch(
                    url,
                    headers={
                        'Authorization': user2_api_key,
                        'Origin': 'http://localhost'
                    }
                )

                # Then
                assert response.status_code == 204
                assert Booking.query.get(booking_id).isUsed is False
                assert Booking.query.get(booking_id).dateUsed is None

            @clean_database
            def expect_booking_to_be_used_with_non_standard_origin_header(self, app):
                # Given
                user = create_user()
                offerer = create_offerer()
                venue = create_venue(offerer)
                stock = create_stock_with_event_offer(offerer, venue, price=0)

                booking = create_booking(user, stock, venue=venue, is_used=True)
                PcObject.save(booking, offerer)

                offererApiKey = create_api_key(offerer, API_KEY_VALUE)

                PcObject.save(offererApiKey)

                booking_id = booking.id

                # When
                user2_api_key = 'Bearer ' + offererApiKey.value
                url = '/v2/bookings/keep/token/{}'.format(booking.token)

                response = TestClient(app.test_client()).patch(
                    url,
                    headers={
                        'Authorization': user2_api_key,
                        'Origin': 'http://random_header.fr'
                    }
                )

                # Then
                assert response.status_code == 204
                assert Booking.query.get(booking_id).isUsed is False
                assert Booking.query.get(booking_id).dateUsed is None

        class WithBasicAuthTest:
            @clean_database
            def when_user_is_logged_in_and_regular_offer(self, app):
                # Given
                user = create_user()
                pro_user = create_user(email='pro@email.fr')
                offerer = create_offerer()
                user_offerer = create_user_offerer(pro_user, offerer)
                venue = create_venue(offerer)
                stock = create_stock_with_event_offer(offerer, venue, price=0)

                booking = create_booking(user, stock, venue=venue, is_used=True)
                PcObject.save(booking, user_offerer)
                booking_id = booking.id

                # When
                url = '/v2/bookings/keep/token/{}'.format(booking.token)
                response = TestClient(app.test_client()).with_auth('pro@email.fr').patch(url)

                # Then
                assert response.status_code == 204
                assert Booking.query.get(booking_id).isUsed is False
                assert Booking.query.get(booking_id).dateUsed is None

            @clean_database
            def when_user_is_logged_in_expect_booking_with_token_in_lower_case_to_be_used(self, app):
                # Given
                user = create_user()
                pro_user = create_user(email='pro@email.fr')
                offerer = create_offerer()
                user_offerer = create_user_offerer(pro_user, offerer)
                venue = create_venue(offerer)
                stock = create_stock_with_event_offer(offerer, venue, price=0)

                booking = create_booking(user, stock, venue=venue, is_used=True)

                PcObject.save(booking, user_offerer)
                booking_id = booking.id
                booking_token = booking.token.lower()

                # When
                url = '/v2/bookings/keep/token/{}'.format(booking_token)
                response = TestClient(app.test_client()).with_auth('pro@email.fr').patch(url)

                # Then
                assert response.status_code == 204
                assert Booking.query.get(booking_id).isUsed is False
                assert Booking.query.get(booking_id).dateUsed is None


            @clean_database
            def when_there_is_no_remaining_quantity_after_validating(self, app):
                # Given
                user = create_user()
                pro_user = create_user(email='pro@email.fr')
                offerer = create_offerer()
                user_offerer = create_user_offerer(pro_user, offerer)
                venue = create_venue(offerer)
                stock = create_stock_with_event_offer(offerer, venue, price=0)
                stock.available=1
                PcObject.save(stock)

                booking = create_booking(user, stock, venue=venue, is_used=True, date_used=datetime.utcnow())
                PcObject.save(booking, user_offerer)

                PcObject.save(booking)

                # When
                PcObject.save(stock)

                url = '/v2/bookings/keep/token/{}'.format(booking.token)
                response = TestClient(app.test_client()).with_auth('pro@email.fr').patch(url)
                stock = Stock.query.one()

                # Then
                assert response.status_code == 204
                assert Booking.query.get(booking.id).dateUsed is None

    class Returns400:
        @clean_database
        def when_there_is_no_remaining_quantity_after_validating(self, app):
            # Given
            user = create_user()
            pro_user = create_user(email='pro@email.fr')
            offerer = create_offerer()
            user_offerer = create_user_offerer(pro_user, offerer)
            venue = create_venue(offerer)
            stock = create_stock_with_event_offer(offerer, venue, price=0)
            stock.available = 1
            PcObject.save(stock)
            booking = create_booking(user, stock, venue=venue, is_used=True, date_used=datetime.utcnow())

            PcObject.save(booking, user_offerer)

            PcObject.save(booking)

            # When
            stock.available = 0
            PcObject.save(stock)

            url = '/v2/bookings/keep/token/{}'.format(booking.token)
            response = TestClient(app.test_client()).with_auth('pro@email.fr').patch(url)

            # Then
            assert response.status_code == 400

    class Returns401:
        @clean_database
        def when_user_not_logged_in_and_doesnt_give_api_key(self, app):
            # Given
            user = create_user(email='user@email.fr')
            offerer = create_offerer()
            venue = create_venue(offerer)
            offer = create_offer_with_event_product(venue, event_name='Event Name')
            event_occurrence = create_event_occurrence(offer)
            stock = create_stock_from_event_occurrence(event_occurrence, price=0)
            booking = create_booking(user, stock, venue=venue)
            
            PcObject.save(booking)

            # When
            url = '/v2/bookings/keep/token/{}'.format(booking.token)
            response = TestClient(app.test_client()).patch(url)

            # Then
            assert response.status_code == 401

        @clean_database
        def when_user_not_logged_in_and_not_existing_api_key_given(self, app):
            # Given
            user = create_user(email='user@email.fr')
            offerer = create_offerer()
            venue = create_venue(offerer)
            offer = create_offer_with_event_product(venue, event_name='Event Name')
            event_occurrence = create_event_occurrence(offer)
            stock = create_stock_from_event_occurrence(event_occurrence, price=0)
            booking = create_booking(user, stock, venue=venue)

            PcObject.save(booking)

            # When
            url = '/v2/bookings/keep/token/{}'.format(booking.token)
            response = TestClient(app.test_client()).patch(url, headers={
                    'Authorization': 'Bearer WrongApiKey1234567',
                    'Origin': 'http://localhost'})

            # Then
            assert response.status_code == 401

    class Returns403:
        class WithApiKeyAuthTest:
            @clean_database
            def when_api_key_given_not_related_to_booking_offerer(self, app):
                # Given
                user = create_user(email='user@email.fr')
                pro_user = create_user(email='pro@email.fr')
                offerer = create_offerer()
                offerer2 = create_offerer(siren='987654321')
                user_offerer = create_user_offerer(pro_user, offerer)
                venue = create_venue(offerer)
                offer = create_offer_with_event_product(venue, event_name='Event Name')
                event_occurrence = create_event_occurrence(offer)
                stock = create_stock_from_event_occurrence(event_occurrence, price=0)
                booking = create_booking(user, stock, venue=venue)

                PcObject.save(pro_user, booking, user_offerer, offerer2)

                offererApiKey = create_api_key(offerer2, API_KEY_VALUE)
                PcObject.save(offererApiKey)

                # When
                user2_api_key = 'Bearer ' + offererApiKey.value
                url = '/v2/bookings/keep/token/{}'.format(booking.token)
                
                response = TestClient(app.test_client()).patch(
                    url,
                    headers={
                        'Authorization': user2_api_key,
                        'Origin': 'http://localhost'}
                )

                # Then
                assert response.status_code == 403
                assert response.json['user'] == [
                    "Vous n'avez pas les droits suffisants pour valider cette contremarque."]

        class WithBasicAuthTest:
            @clean_database
            def when_user_is_not_attached_to_linked_offerer(self, app):
                # Given
                user = create_user()
                pro_user = create_user(email='pro@email.fr')
                offerer = create_offerer()
                venue = create_venue(offerer)
                stock = create_stock_with_event_offer(offerer, venue, price=0)

                booking = create_booking(user, stock, venue=venue)
                PcObject.save(booking, pro_user)

                # When
                url = '/v2/bookings/keep/token/{}?email={}'.format(booking.token, user.email)
                response = TestClient(app.test_client()).with_auth('pro@email.fr').patch(url)

                # Then
                assert response.status_code == 403
                assert response.json['user'] == [
                    "Vous n'avez pas les droits suffisants pour valider cette contremarque."]
                assert Booking.query.get(booking.id).isUsed is False

            @clean_database
            def when_user_is_admin_and_tries_to_patch_activation_offer(self, app):
                # Given
                user = create_user()
                admin_user = create_user(email='admin@email.fr', is_admin=True, can_book_free_offers=False)

                offerer = create_offerer()
                user_offerer = create_user_offerer(admin_user, offerer)
                venue = create_venue(offerer)

                activation_offer = create_offer_with_event_product(venue, event_type=EventType.ACTIVATION)
                activation_event_occurrence = create_event_occurrence(activation_offer)
                stock = create_stock_from_event_occurrence(activation_event_occurrence, price=0)

                booking = create_booking(user, stock, venue=venue)

                PcObject.save(booking, user_offerer)

                # When
                url = '/v2/bookings/keep/token/{}'.format(booking.token)
                response = TestClient(app.test_client()).with_auth('admin@email.fr').patch(url)

                # Then
                assert response.status_code == 403
                assert Booking.query.get(booking.id).isUsed is False
                assert response.json['booking'] == [
                    "Seuls les administrateurs du pass Culture peuvent annuler des offres d'activation."]

    class Returns404:
        class WithApiKeyAuthTest:
            @clean_database
            def when_booking_is_not_provided_at_all(self, app):
                # Given
                user = create_user(email='user@email.fr')
                offerer = create_offerer()
                venue = create_venue(offerer)
                offer = create_offer_with_event_product(venue, event_name='Event Name')
                event_occurrence = create_event_occurrence(offer)
                stock = create_stock_from_event_occurrence(event_occurrence, price=0)

                booking = create_booking(user, stock, venue=venue)

                PcObject.save(booking)

                offererApiKey = create_api_key(offerer, API_KEY_VALUE)
                PcObject.save(offererApiKey)

                # When
                url = '/v2/bookings/keep/token/'
                user2_api_key = 'Bearer ' + offererApiKey.value

                response = TestClient(app.test_client()).patch(
                    url,
                    headers={
                        'Authorization': user2_api_key,
                        'Origin': 'http://localhost'
                    }
                )

                # Then
                assert response.status_code == 404

            @clean_database
            def when_api_key_is_provided_and_booking_does_not_exist(self, app):
                # Given
                user = create_user()
                offerer = create_offerer()
                venue = create_venue(offerer)
                stock = create_stock_with_event_offer(offerer, venue, price=0)

                booking = create_booking(user, stock, venue=venue)
                PcObject.save(booking)

                offererApiKey = create_api_key(offerer, API_KEY_VALUE)
                PcObject.save(offererApiKey)

                # When
                url = '/v2/bookings/keep/token/{}'.format('456789')
                user2_api_key = 'Bearer ' + offererApiKey.value

                response = TestClient(app.test_client()).patch(
                    url,
                    headers={
                        'Authorization': user2_api_key,
                        'Origin': 'http://localhost'
                    }
                )

                # Then
                assert response.status_code == 404
                assert response.json['global'] == ["Cette contremarque n'a pas été trouvée"]

        class WithBasicAuthTest:
            @clean_database
            def when_user_is_logged_in_and_booking_does_not_exist(self, app):
                # Given
                user = create_user()
                pro_user= create_user(email='pro@email.fr')
                offerer = create_offerer()
                user_offerer = create_user_offerer(pro_user, offerer)
                venue = create_venue(offerer)
                stock = create_stock_with_event_offer(offerer, venue, price=0)

                booking = create_booking(user, stock, venue=venue)
                PcObject.save(booking, user_offerer)

                # When
                url = '/v2/bookings/keep/token/{}'.format('123456')
                response = TestClient(app.test_client()).with_auth('pro@email.fr').patch(url)

                # Then
                assert response.status_code == 404
                assert response.json['global'] == ["Cette contremarque n'a pas été trouvée"]

            @clean_database
            def when_user_is_logged_in_and_booking_toke_is_null(self, app):
                # Given
                user = create_user()
                pro_user = create_user(email='pro@email.fr')
                offerer = create_offerer()
                user_offerer = create_user_offerer(pro_user, offerer)
                venue = create_venue(offerer)
                stock = create_stock_with_event_offer(offerer, venue, price=0)

                booking = create_booking(user, stock, venue=venue)

                PcObject.save(booking, user_offerer)

                # When
                url = '/v2/bookings/keep/token/'
                response = TestClient(app.test_client()).with_auth('pro@email.fr').patch(url)

                # Then
                assert response.status_code == 404

    class Returns410:
        class WithBasicAuthTest:
            @clean_database
            def when_user_is_logged_in_and_booking_has_been_cancelled_already(self, app):
                # Given
                user = create_user()
                pro_user = create_user(email='pro@email.fr')
                offerer = create_offerer()
                user_offerer = create_user_offerer(pro_user, offerer)
                venue = create_venue(offerer)
                stock = create_stock_with_event_offer(offerer, venue, price=0)

                booking = create_booking(user, stock, venue=venue, is_used=True)

                booking.isCancelled = True
                PcObject.save(booking, user_offerer)

                # When
                url = '/v2/bookings/keep/token/{}'.format(booking.token)
                response = TestClient(app.test_client()).with_auth('pro@email.fr').patch(url)

                # Then
                assert response.status_code == 410
                assert response.json['booking'] == ['Cette réservation a été annulée']
                assert Booking.query.get(booking.id).isUsed is True

            @clean_database
            def when_user_is_logged_in_and_booking_has_not_been_validated_already(self, app):
                # Given
                user = create_user()
                pro_user = create_user(email='pro@email.fr')
                offerer = create_offerer()
                user_offerer = create_user_offerer(pro_user, offerer)
                venue = create_venue(offerer)
                stock = create_stock_with_event_offer(offerer, venue, price=0)

                booking = create_booking(user, stock, venue=venue)
                PcObject.save(booking, user_offerer)

                # When
                url = '/v2/bookings/keep/token/{}'.format(booking.token)
                response = TestClient(app.test_client()).with_auth('pro@email.fr').patch(url)

                # Then
                assert response.status_code == 410
                assert response.json['booking'] == ["Cette réservation n'a encore été validée"]
                assert Booking.query.get(booking.id).isUsed is False

            @clean_database
            def when_user_is_logged_in_and_booking_payment_exists(self, app):
                # Given
                user = create_user()
                pro_user = create_user(email='pro@email.fr')
                offerer = create_offerer()
                user_offerer = create_user_offerer(pro_user, offerer)
                venue = create_venue(offerer)
                stock = create_stock_with_event_offer(offerer, venue, price=0)

                booking = create_booking(user, stock, venue=venue)
                payment = create_payment(booking, offerer, Decimal(10), iban='CF13QSDFGH456789', bic='QSDFGH8Z555')

                PcObject.save(booking, user_offerer, payment)

                # When
                url = '/v2/bookings/keep/token/{}'.format(booking.token)
                response = TestClient(app.test_client()).with_auth('pro@email.fr').patch(url)

                # Then
                assert response.status_code == 410
                assert response.json['payment'] == ["Le remboursement est en cours de traitement"]
                assert Booking.query.get(booking.id).isUsed is False

        class WithApiKeyAuthTest:
            @clean_database
            def when_api_key_is_provided_and_booking_has_been_cancelled_already(self, app):
                # Given
                user = create_user()
                pro_user = create_user(email='pro@email.fr')

                offerer = create_offerer()
                user_offerer = create_user_offerer(pro_user, offerer)
                venue = create_venue(offerer)

                stock = create_stock_with_event_offer(offerer, venue, price=0)

                booking = create_booking(user, stock, venue=venue, is_used=True)
                booking.isCancelled = True

                PcObject.save(booking, user_offerer)

                offererApiKey = create_api_key(offerer, API_KEY_VALUE)
                PcObject.save(offererApiKey)

                # When
                url = '/v2/bookings/keep/token/{}'.format(booking.token)
                user2_api_key = 'Bearer ' + offererApiKey.value

                response = TestClient(app.test_client()).patch(
                    url,
                    headers={
                        'Authorization': user2_api_key,
                        'Origin': 'http://localhost'
                    }
                )

                # Then
                assert response.status_code == 410
                assert response.json['booking'] == ['Cette réservation a été annulée']
                assert Booking.query.get(booking.id).isUsed is True

            @clean_database
            def when_api_key_is_provided_and_booking_has_not_been_validated_already(self, app):
                # Given
                user = create_user()
                pro_user = create_user(email='pro@email.fr')
                offerer = create_offerer()
                user_offerer = create_user_offerer(pro_user, offerer)
                venue = create_venue(offerer)
                stock = create_stock_with_event_offer(offerer, venue, price=0)
                booking = create_booking(user, stock, venue=venue)
                PcObject.save(booking, user_offerer)

                offererApiKey = create_api_key(offerer, API_KEY_VALUE)
                PcObject.save(offererApiKey)

                # When
                url = '/v2/bookings/keep/token/{}'.format(booking.token)
                user2_api_key = 'Bearer ' + offererApiKey.value

                response = TestClient(app.test_client()).patch(
                    url,
                    headers={
                        'Authorization': user2_api_key,
                        'Origin': 'http://localhost'
                    }
                )
                # Then
                assert response.status_code == 410
                assert response.json['booking'] == ["Cette réservation n'a encore été validée"]
                assert Booking.query.get(booking.id).isUsed is False

            @clean_database
            def when_api_key_is_provided_and_booking_payment_exists(self, app):
                # Given
                user = create_user()
                pro_user = create_user(email='pro@email.fr')
                offerer = create_offerer()
                user_offerer = create_user_offerer(pro_user, offerer)
                venue = create_venue(offerer)
                stock = create_stock_with_event_offer(offerer, venue, price=0)

                booking = create_booking(user, stock, venue=venue)
                payment = create_payment(booking, offerer, Decimal(10), iban='CF13QSDFGH456789', bic='QSDFGH8Z555')

                PcObject.save(booking, user_offerer, payment)

                offererApiKey = create_api_key(offerer, API_KEY_VALUE)
                PcObject.save(offererApiKey)

                # When
                url = '/v2/bookings/keep/token/{}'.format(booking.token)
                user2_api_key = 'Bearer ' + offererApiKey.value

                response = TestClient(app.test_client()).patch(
                    url,
                    headers={
                        'Authorization': user2_api_key,
                        'Origin': 'http://localhost'
                    }
                )
                # Then
                assert response.status_code == 410
                assert response.json['payment'] == ["Le remboursement est en cours de traitement"]
                assert Booking.query.get(booking.id).isUsed is False
