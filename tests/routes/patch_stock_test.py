from datetime import timedelta
from sqlalchemy_api_handler import ApiHandler, humanize
from sqlalchemy_api_handler.serialization.serialize import serialize

from models import Stock, Provider
from tests.conftest import clean_database, TestClient
from tests.test_utils import create_booking, create_user, create_user_offerer, create_offerer, create_venue, \
    create_stock_with_event_offer, create_stock_with_thing_offer, create_stock, create_offer_with_thing_product


class Patch:
    class Returns200:
        @clean_database
        def when_user_has_editor_rights_on_offerer(self, app):
            # given
            user = create_user(email='test@email.com')
            offerer = create_offerer()
            user_offerer = create_user_offerer(user, offerer)
            venue = create_venue(offerer)
            stock = create_stock_with_event_offer(offerer, venue, price=10, available=10)
            ApiHandler.save(user, user_offerer, stock)
            humanized_stock_id = humanize(stock.id)

            # when
            request_update = TestClient(app.test_client()).with_auth('test@email.com') \
                .patch('/stocks/' + humanized_stock_id, json={'available': 5, 'price': 20})

            # then
            assert request_update.status_code == 200
            request_after_update = TestClient(app.test_client()).with_auth('test@email.com').get(
                '/stocks/' + humanized_stock_id)
            assert request_after_update.json['available'] == 5
            assert request_after_update.json['price'] == 20

        @clean_database
        def when_user_is_admin(self, app):
            # given
            user = create_user(email='test@email.com', can_book_free_offers=False, is_admin=True)
            offerer = create_offerer()
            venue = create_venue(offerer)
            stock = create_stock_with_event_offer(offerer, venue, price=10, available=10)
            ApiHandler.save(user, stock)
            humanized_stock_id = humanize(stock.id)

            # when
            request_update = TestClient(app.test_client()).with_auth('test@email.com') \
                .patch('/stocks/' + humanized_stock_id, json={'available': 5, 'price': 20})

            # then
            assert request_update.status_code == 200
            request_after_update = TestClient(app.test_client()).with_auth('test@email.com').get(
                '/stocks/' + humanized_stock_id)
            assert request_after_update.json['available'] == 5
            assert request_after_update.json['price'] == 20

        @clean_database
        def when_booking_limit_datetime_is_none_for_thing(self, app):
            # Given
            user = create_user(email='test@email.fr', can_book_free_offers=False, is_admin=True)
            offerer = create_offerer()
            venue = create_venue(offerer)
            stock = create_stock_with_thing_offer(offerer, venue)
            ApiHandler.save(user, stock)
            stock_id = stock.id

            data = {
                'price': 120,
                'offerId': humanize(stock.offer.id),
                'bookingLimitDatetime': None
            }

            # When
            response = TestClient(app.test_client()).with_auth(user.email) \
                .patch('/stocks/' + humanize(stock.id), json=data)

            # Then
            assert response.status_code == 200
            assert Stock.query.get(stock_id).price == 120

        @clean_database
        def when_available_below_number_of_already_existing_bookings(self, app):
            # given
            user = create_user()
            user_admin = create_user(email='email@test.com', can_book_free_offers=False, is_admin=True)
            offerer = create_offerer()
            venue = create_venue(offerer)
            stock = create_stock_with_event_offer(offerer, venue, price=0)
            stock.available = 1
            booking = create_booking(user, stock, venue, recommendation=None)
            ApiHandler.save(booking, user_admin)

            # when
            response = TestClient(app.test_client()).with_auth('email@test.com') \
                .patch('/stocks/' + humanize(stock.id), json={'available': 0})

            # then
            assert response.status_code == 200
            assert 'available' in response.json

    class Returns400:
        @clean_database
        def when_wrong_type_for_available(self, app):
            # given
            user = create_user()
            user_admin = create_user(email='email@test.com', can_book_free_offers=False, is_admin=True)
            offerer = create_offerer()
            venue = create_venue(offerer)
            stock = create_stock_with_event_offer(offerer, venue, price=0)
            stock.available = 1
            booking = create_booking(user, stock, venue, recommendation=None)
            ApiHandler.save(booking, user_admin)

            # when
            response = TestClient(app.test_client()).with_auth('email@test.com') \
                .patch('/stocks/' + humanize(stock.id), json={'available': ' '})

            # then
            assert response.status_code == 400
            assert response.json['available'] == ['Saisissez un nombre valide']

        @clean_database
        def when_booking_limit_datetime_after_beginning_datetime(self, app):
            # given
            user = create_user(email='email@test.com', can_book_free_offers=False, is_admin=True)
            offerer = create_offerer()
            venue = create_venue(offerer)
            stock = create_stock_with_event_offer(offerer, venue)
            ApiHandler.save(stock, user)
            stockId = stock.id
            serialized_date = serialize(stock.beginningDatetime + timedelta(days=1))

            # when
            response = TestClient(app.test_client()).with_auth('email@test.com') \
                .patch('/stocks/' + humanize(stockId), json={'bookingLimitDatetime': serialized_date})

            # then
            assert response.status_code == 400
            assert response.json['bookingLimitDatetime'] == [
                'La date limite de réservation pour cette offre est postérieure à la date de début de l\'évènement'
            ]

        @clean_database
        def when_end_limit_datetime_is_none_for_event(self, app):
            # given
            user = create_user(email='email@test.com', can_book_free_offers=False, is_admin=True)
            offerer = create_offerer()
            venue = create_venue(offerer)
            stock = create_stock_with_event_offer(offerer, venue)
            ApiHandler.save(stock, user)

            # when
            response = TestClient(app.test_client()).with_auth('email@test.com') \
                .patch('/stocks/' + humanize(stock.id), json={'endDatetime': None})

            # then
            assert response.status_code == 400
            assert response.json['endDatetime'] == ['Ce paramètre est obligatoire']

        @clean_database
        def when_booking_limit_datetime_is_none_for_event(self, app):
            # Given
            user = create_user(email='test@email.fr', can_book_free_offers=False, is_admin=True)
            offerer = create_offerer()
            venue = create_venue(offerer)
            stock = create_stock_with_event_offer(offerer, venue)
            ApiHandler.save(user, stock)

            data = {
                'price': 0,
                'offerId': humanize(stock.offer.id),
                'bookingLimitDatetime': None
            }

            # When
            response = TestClient(app.test_client()).with_auth(user.email) \
                .patch('/stocks/' + humanize(stock.id), json=data)

            # Then
            assert response.status_code == 400
            assert response.json["bookingLimitDatetime"] == ['Ce paramètre est obligatoire']

        @clean_database
        def when_offer_come_from_provider(self, app):
            # given
            tite_live_provider = Provider \
                .query \
                .filter(Provider.localClass == 'TiteLiveThings') \
                .first()

            user = create_user(email='test@email.com')
            offerer = create_offerer()
            user_offerer = create_user_offerer(user, offerer)
            venue = create_venue(offerer)
            offer = create_offer_with_thing_product(venue, last_provider_id=tite_live_provider.id)
            stock = create_stock(offer=offer, available=10)
            ApiHandler.save(user, user_offerer, stock)
            humanized_stock_id = humanize(stock.id)

            # when
            request_update = TestClient(app.test_client()).with_auth('test@email.com') \
                .patch('/stocks/' + humanized_stock_id, json={'available': 5})

            # then
            assert request_update.status_code == 400
            request_after_update = TestClient(app.test_client()).with_auth('test@email.com').get(
                '/stocks/' + humanized_stock_id)
            assert request_after_update.json['available'] == 10
            assert request_update.json["global"] == ["Les offres importées ne sont pas modifiables"]

    class Returns403:
        @clean_database
        def when_user_has_no_rights(self, app):
            # given
            user = create_user(email='test@email.com')
            offerer = create_offerer()
            venue = create_venue(offerer)
            stock = create_stock_with_event_offer(offerer, venue)
            ApiHandler.save(user, stock)

            # when
            response = TestClient(app.test_client()).with_auth('test@email.com') \
                .patch('/stocks/' + humanize(stock.id), json={'available': 5})

            # then
            assert response.status_code == 403
            assert "Vous n'avez pas les droits d'accès suffisant pour accéder à cette information." in response.json[
                'global']
