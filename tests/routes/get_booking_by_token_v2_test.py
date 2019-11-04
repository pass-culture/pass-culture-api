from datetime import datetime, timedelta

from models import ApiKey, PcObject, EventType
from tests.conftest import clean_database, TestClient
from tests.test_utils import create_stock_with_thing_offer, \
    create_venue, create_offerer, \
    create_user, create_booking, create_offer_with_event_product, \
    create_event_occurrence, create_stock_from_event_occurrence, create_user_offerer, create_stock_with_event_offer, \
    create_api_key
from utils.token import random_token

API_KEY_VALUE = random_token(64)

class Get:
    class Returns200:
        @clean_database
        def when_user_has_rights_and_regular_offer(self, app):
            # Given
            user = create_user(public_name='John Doe', email='user@email.fr')
            admin_user = create_user(email='admin@email.fr')
            offerer = create_offerer()
            user_offerer = create_user_offerer(admin_user, offerer)
            venue = create_venue(offerer)
            offer = create_offer_with_event_product(venue, event_name='Event Name', event_type=EventType.CINEMA)
            event_occurrence = create_event_occurrence(offer)
            stock = create_stock_from_event_occurrence(event_occurrence, price=0)
            booking = create_booking(user, stock, venue=venue)

            PcObject.save(user_offerer, booking)
            url = '/v2/bookings/token/{}'.format(booking.token)

            # When
            response = TestClient(app.test_client()).with_auth('admin@email.fr').get(url)

            # Then
            assert response.headers['Content-type'] == 'application/json'
            assert response.status_code == 200

        @clean_database
        def when_api_key_is_provided_and_rights_and_regular_offer(self, app):
            # Given
            user = create_user(public_name='John Doe', email='user@email.fr')
            user2 = create_user(public_name='Jane Doe', email='user2@email.fr')
            offerer = create_offerer()
            user_offerer = create_user_offerer(user2, offerer)
            venue = create_venue(offerer)
            offer = create_offer_with_event_product(venue, event_name='Event Name', event_type=EventType.CINEMA)
            event_occurrence = create_event_occurrence(offer)
            stock = create_stock_from_event_occurrence(event_occurrence, price=0)
            booking = create_booking(user, stock, venue=venue)

            PcObject.save(user_offerer, booking)

            offererApiKey = create_api_key(offerer, API_KEY_VALUE)
            PcObject.save(offererApiKey)

            user2ApiKey = 'Bearer ' + offererApiKey.value
            booking_token = booking.token.lower()
            url = '/v2/bookings/token/{}'.format(booking_token)

            # When
            response = TestClient(app.test_client()).get(
                url,
                headers={
                    'Authorization': user2ApiKey,
                    'Origin': 'http://localhost'}
            )

            # Then
            assert response.status_code == 200

        @clean_database
        def when_there_is_not_enough_available_stock_to_validate_a_booking(self, app):
            # Given
            user = create_user()
            pro_user = create_user(email='pro@email.fr', is_admin=False)
            offerer = create_offerer()
            user_offerer = create_user_offerer(pro_user, offerer)
            venue = create_venue(offerer)
            stock = create_stock_with_event_offer(offerer, venue, price=0)
            booking = create_booking(user, stock, venue=venue)
            PcObject.save(booking, user_offerer)
            url = '/v2/bookings/token/{}'.format(booking.token)

            stock.available = 0
            PcObject.save(stock)

            # When
            response = TestClient(app.test_client()).with_auth('pro@email.fr').get(url)

            # Then
            assert response.status_code == 200

        @clean_database
        def when_user_has_rights_and_regular_offer_and_token_in_lower_case(self, app):
            # Given
            user = create_user(public_name='John Doe', email='user@email.fr')
            admin_user = create_user(email='admin@email.fr')
            offerer = create_offerer()
            user_offerer = create_user_offerer(admin_user, offerer)
            venue = create_venue(offerer)
            offer = create_offer_with_event_product(venue, event_name='Event Name', event_type=EventType.CINEMA)
            event_occurrence = create_event_occurrence(offer)
            stock = create_stock_from_event_occurrence(event_occurrence, price=0)
            booking = create_booking(user, stock, venue=venue)

            PcObject.save(user_offerer, booking)

            booking_token = booking.token.lower()
            url = '/v2/bookings/token/{}'.format(booking_token)

            # When
            response = TestClient(app.test_client()).with_auth('admin@email.fr').get(url)

            # Then
            assert response.status_code == 200

        @clean_database
        def when_non_standard_origin_header(self, app):
            # Given
            user = create_user()
            admin_user = create_user(email='admin@email.fr')
            offerer = create_offerer()
            user_offerer = create_user_offerer(admin_user, offerer)
            venue = create_venue(offerer)
            stock = create_stock_with_event_offer(offerer, venue, price=0)
            booking = create_booking(user, stock, venue=venue)
            PcObject.save(booking, user_offerer)
            url = '/v2/bookings/token/{}'.format(booking.token)

            # When
            response = TestClient(app.test_client()) \
                .with_auth('admin@email.fr') \
                .get(url, headers={'origin': 'http://random_header.fr'})

            # Then
            assert response.status_code == 200

        @clean_database
        def when_activation_event_and_user_has_rights(self, app):
            # Given
            user = create_user(email='user@email.fr', phone_number='0698765432', date_of_birth=datetime(2001, 2, 1))
            admin_user = create_user(email='admin@email.fr', is_admin=True, can_book_free_offers=False)
            offerer = create_offerer()
            venue = create_venue(offerer)
            offer = create_offer_with_event_product(venue, event_name='Offre d\'activation',
                                                    event_type=EventType.ACTIVATION)
            event_occurrence = create_event_occurrence(offer)
            stock = create_stock_from_event_occurrence(event_occurrence, price=0)
            booking = create_booking(user, stock, venue=venue)

            PcObject.save(admin_user, booking)

            # When
            response = TestClient(app.test_client()) \
                .with_auth('admin@email.fr') \
                .get('/v2/bookings/token/{}'.format(booking.token))

            # Then
            assert response.status_code == 200

    class Returns401:
        @clean_database
        def when_user_not_logged_in_and_doesnt_give_api_key(self, app):
            # Given
            user = create_user(email='user@email.fr')
            admin_user = create_user(email='admin@email.fr')
            offerer = create_offerer()
            venue = create_venue(offerer)
            offer = create_offer_with_event_product(venue, event_name='Event Name')
            event_occurrence = create_event_occurrence(offer)
            stock = create_stock_from_event_occurrence(event_occurrence, price=0)
            booking = create_booking(user, stock, venue=venue)

            PcObject.save(admin_user, booking)

            url = '/v2/bookings/token/{}'.format(booking.token)

            # When
            response = TestClient(app.test_client()).get(url)

            # Then
            assert response.status_code == 401

        @clean_database
        def when_user_not_logged_in_and_not_existing_api_key_given(self, app):
            # Given
            user = create_user(email='user@email.fr')
            admin_user = create_user(email='admin@email.fr')
            offerer = create_offerer()
            venue = create_venue(offerer)
            offer = create_offer_with_event_product(venue, event_name='Event Name')
            event_occurrence = create_event_occurrence(offer)
            stock = create_stock_from_event_occurrence(event_occurrence, price=0)
            booking = create_booking(user, stock, venue=venue)

            PcObject.save(admin_user, booking)

            url = '/v2/bookings/token/{}'.format(booking.token)

            # When
            response = TestClient(app.test_client()).get(url, headers={
                    'Authorization': 'Bearer WrongApiKey1234567',
                    'Origin': 'http://localhost'})

            # Then
            assert response.status_code == 401


    class Returns403:
        @clean_database
        def when_user_doesnt_have_rights_and_token_exists(self, app):
            # Given
            user = create_user(email='user@email.fr')
            querying_user = create_user(email='querying@email.fr')
            offerer = create_offerer()
            venue = create_venue(offerer)
            offer = create_offer_with_event_product(venue, event_name='Event Name')
            event_occurrence = create_event_occurrence(offer)
            stock = create_stock_from_event_occurrence(event_occurrence, price=0)
            booking = create_booking(user, stock, venue=venue)

            PcObject.save(querying_user, booking)

            url = '/v2/bookings/token/{}'.format(booking.token)

            # When
            response = TestClient(app.test_client()).with_auth('querying@email.fr').get(url)

            # Then
            assert response.status_code == 403
            assert response.json['user'] == ["Vous n'avez pas les droits suffisants pour éditer cette contremarque."]

        @clean_database
        def when_api_key_given_not_related_to_booking_offerer(self, app):
            # Given
            user = create_user(email='user@email.fr')
            admin_user = create_user(email='admin@email.fr')
            offerer = create_offerer()
            offerer2 = create_offerer(siren='987654321')
            user_offerer = create_user_offerer(admin_user, offerer)

            venue = create_venue(offerer)
            offer = create_offer_with_event_product(venue, event_name='Event Name')
            event_occurrence = create_event_occurrence(offer)
            stock = create_stock_from_event_occurrence(event_occurrence, price=0)
            booking = create_booking(user, stock, venue=venue)

            PcObject.save(admin_user, booking, user_offerer, offerer2)

            offererApiKey = create_api_key(offerer, API_KEY_VALUE)

            PcObject.save(offererApiKey)

            user2ApiKey = 'Bearer ' + offererApiKey.value
            url = '/v2/bookings/token/{}'.format(booking.token)

            # When
            response = TestClient(app.test_client()).get(
                url,
                headers={
                    'Authorization': user2ApiKey,
                    'Origin': 'http://localhost'}
            )

            # Then
            assert response.status_code == 403
            assert response.json['user'] == ["Vous n'avez pas les droits suffisants pour éditer cette contremarque."]


        @clean_database
        def when_booking_is_on_stock_with_beginning_datetime_in_more_than_72_hours(self, app):
            # Given
            in_73_hours = datetime.utcnow() + timedelta(hours=73)
            in_74_hours = datetime.utcnow() + timedelta(hours=74)
            in_72_hours = datetime.utcnow() + timedelta(hours=72)
            user = create_user(email='user@email.fr')
            admin_user = create_user(email='admin@email.fr')
            offerer = create_offerer()
            user_offerer = create_user_offerer(admin_user, offerer)
            venue = create_venue(offerer)
            stock = create_stock_with_event_offer(offerer, venue, price=0, beginning_datetime=in_73_hours,
            end_datetime=in_74_hours, booking_limit_datetime=in_72_hours)
            booking = create_booking(user, stock, venue=venue)

            PcObject.save(admin_user, booking, user_offerer)

            url = '/v2/bookings/token/{}'.format(booking.token)

            # When
            response = TestClient(app.test_client()).with_auth('admin@email.fr').get(url)

            # Then
            assert response.status_code == 403
            assert response.json['beginningDatetime'] == [
            'Vous ne pouvez pas valider cette contremarque plus de 72h avant le début de l\'évènement']


    class Returns404:
        @clean_database
        def when_token_user_has_rights_but_token_not_found(self, app):
            # Given
            admin_user = create_user(email='admin@email.fr')
            PcObject.save(admin_user)

            url = '/v2/bookings/token/{}'.format('12345')

            # When
            response = TestClient(app.test_client()).with_auth('admin@email.fr').get(url)

            # Then
            assert response.status_code == 404
            assert response.json['global'] == ["Cette contremarque n'a pas été trouvée"]

        @clean_database
        def when_user_has_api_key_but_token_not_found(self, app):
            # Given
            user = create_user(email='user@email.fr')
            admin_user = create_user(email='admin@email.fr')
            offerer = create_offerer()
            user_offerer = create_user_offerer(admin_user, offerer)
            venue = create_venue(offerer)
            offer = create_offer_with_event_product(venue, event_name='Event Name')
            event_occurrence = create_event_occurrence(offer)
            stock = create_stock_from_event_occurrence(event_occurrence, price=0)
            booking = create_booking(user, stock, venue=venue)

            PcObject.save(admin_user, booking, user_offerer)

            offererApiKey = create_api_key(offerer, API_KEY_VALUE)

            PcObject.save(offererApiKey)

            user2ApiKey = 'Bearer ' + offererApiKey.value
            url = '/v2/bookings/token/{}'.format('12345')

            # When
            response = TestClient(app.test_client()).get(
                url,
                headers={
                    'Authorization': user2ApiKey,
                    'Origin': 'http://localhost'}
            )

            # Then
            assert response.status_code == 404
            assert response.json['global'] == ["Cette contremarque n'a pas été trouvée"]

    class Returns410:
        @clean_database
        def when_booking_is_already_validated(self, app):
            # Given
            user = create_user(email='user@email.fr')
            admin_user = create_user(email='admin@email.fr')
            offerer = create_offerer()
            user_offerer = create_user_offerer(admin_user, offerer)

            venue = create_venue(offerer)
            stock = create_stock_with_thing_offer(offerer, venue, offer=None, price=0)
            booking = create_booking(user, stock, venue=venue, is_used=True)

            PcObject.save(admin_user, booking, user_offerer)

            offererApiKey = create_api_key(offerer, API_KEY_VALUE)

            PcObject.save(offererApiKey)

            user2ApiKey = 'Bearer ' + offererApiKey.value
            url = '/v2/bookings/token/{}'.format(booking.token)

            # When
            response = TestClient(app.test_client()).get(
                url,
                headers={
                    'Authorization': user2ApiKey,
                    'Origin': 'http://localhost'}
            )

            # Then
            assert response.status_code == 410
            assert response.json['booking'] == ['Cette réservation a déjà été validée']

        @clean_database
        def when_booking_is_cancelled(self, app):
            # Given
            user = create_user(email='user@email.fr')
            admin_user = create_user(email='admin@email.fr')
            offerer = create_offerer()
            user_offerer = create_user_offerer(admin_user, offerer)
            venue = create_venue(offerer)
            stock = create_stock_with_thing_offer(offerer, venue, offer=None, price=0)
            booking = create_booking(user, stock, venue=venue, is_cancelled=True)

            PcObject.save(admin_user, booking, user_offerer)

            offererApiKey = create_api_key(offerer, API_KEY_VALUE)

            PcObject.save(offererApiKey)

            user2ApiKey = 'Bearer ' + offererApiKey.value
            url = '/v2/bookings/token/{}'.format(booking.token)

            # When
            response = TestClient(app.test_client()).get(
                url,
                headers={
                    'Authorization': user2ApiKey,
                    'Origin': 'http://localhost'}
            )

            # Then
            assert response.status_code == 410
            assert response.json['booking'] == ['Cette réservation a été annulée']
