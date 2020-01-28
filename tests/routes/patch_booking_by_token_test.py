from urllib.parse import urlencode

from models import EventType, ThingType, Deposit, Booking, User
from repository import repository
from tests.conftest import clean_database, TestClient
from tests.model_creators.generic_creators import create_booking, create_user, create_offerer, create_venue, \
    create_deposit, \
    create_user_offerer
from tests.model_creators.specific_creators import create_stock_with_event_offer, create_stock_from_event_occurrence, \
    create_offer_with_event_product, create_event_occurrence
from utils.human_ids import humanize


class Patch:
    class Returns204:
        class WhenUserIsAnonymous:
            @clean_database
            def expect_booking_to_be_used(self, app):
                # Given
                user = create_user()
                offerer = create_offerer()
                venue = create_venue(offerer)
                stock = create_stock_with_event_offer(offerer, venue, price=0)
                booking = create_booking(user=user, stock=stock, venue=venue)
                repository.save(booking)
                booking_id = booking.id
                url = '/bookings/token/{}?email={}&offer_id={}'.format(booking.token, user.email,
                                                                       humanize(stock.resolvedOffer.id))

                # When
                response = TestClient(app.test_client()).patch(url)

                # Then
                assert response.status_code == 204
                assert Booking.query.get(booking_id).isUsed is True

        class WhenUserIsLoggedIn:
            @clean_database
            def expect_booking_to_be_used(self, app):
                # Given
                user = create_user()
                admin_user = create_user(email='admin@email.fr')
                offerer = create_offerer()
                user_offerer = create_user_offerer(admin_user, offerer)
                venue = create_venue(offerer)
                stock = create_stock_with_event_offer(offerer, venue, price=0)
                booking = create_booking(user=user, stock=stock, venue=venue)
                repository.save(booking, user_offerer)
                booking_id = booking.id
                url = '/bookings/token/{}'.format(booking.token)

                # When
                response = TestClient(app.test_client()).with_auth('admin@email.fr').patch(url)

                # Then
                assert response.status_code == 204
                assert Booking.query.get(booking_id).isUsed is True

            @clean_database
            def expect_booking_with_token_in_lower_case_to_be_used(self, app):
                # Given
                user = create_user()
                admin_user = create_user(email='admin@email.fr')
                offerer = create_offerer()
                user_offerer = create_user_offerer(admin_user, offerer)
                venue = create_venue(offerer)
                stock = create_stock_with_event_offer(offerer, venue, price=0)
                booking = create_booking(user=user, stock=stock, venue=venue)
                repository.save(booking, user_offerer)
                booking_id = booking.id
                booking_token = booking.token.lower()
                url = '/bookings/token/{}'.format(booking_token)

                # When
                response = TestClient(app.test_client()).with_auth('admin@email.fr').patch(url)

                # Then
                assert response.status_code == 204
                assert Booking.query.get(booking_id).isUsed is True

            @clean_database
            def expect_booking_to_be_used_with_non_standard_origin_header(self, app):
                # Given
                user = create_user()
                admin_user = create_user(email='admin@email.fr')
                offerer = create_offerer()
                user_offerer = create_user_offerer(admin_user, offerer)
                venue = create_venue(offerer)
                stock = create_stock_with_event_offer(offerer, venue, price=0)
                booking = create_booking(user=user, stock=stock, venue=venue)
                repository.save(booking, user_offerer)
                booking_id = booking.id
                url = '/bookings/token/{}'.format(booking.token)

                # When
                response = TestClient(app.test_client()) \
                    .with_auth('admin@email.fr') \
                    .patch(url, headers={'origin': 'http://random_header.fr'})

                # Then
                assert response.status_code == 204
                assert Booking.query.get(booking_id).isUsed is True

            @clean_database
            def expect_booking_to_be_used_with_special_char_in_url(self, app):
                # Given
                user = create_user(email='user+plus@email.fr')
                user_admin = create_user(email='admin@email.fr')
                offerer = create_offerer()
                user_offerer = create_user_offerer(user_admin, offerer, is_admin=True)
                venue = create_venue(offerer)
                offer = create_offer_with_event_product(venue, event_name='Event Name')
                event_occurrence = create_event_occurrence(offer)
                stock = create_stock_from_event_occurrence(event_occurrence, price=0)
                booking = create_booking(user=user, stock=stock, venue=venue)

                repository.save(user_offerer, booking)
                url_email = urlencode({'email': 'user+plus@email.fr'})
                url = '/bookings/token/{}?{}'.format(booking.token, url_email)

                # When
                response = TestClient(app.test_client()).with_auth('admin@email.fr').patch(url)
                # Then
                assert response.status_code == 204

        class WhenUserIsAdmin:
            @clean_database
            def expect_activation_booking_to_be_used_and_linked_user_to_be_able_to_book(self, app):
                # Given
                user = create_user(can_book_free_offers=False, is_admin=False, first_name='John')
                pro_user = create_user(can_book_free_offers=False, email='pro@email.fr', is_admin=True)
                offerer = create_offerer()
                user_offerer = create_user_offerer(pro_user, offerer)
                venue = create_venue(offerer)
                activation_offer = create_offer_with_event_product(venue, event_type=ThingType.ACTIVATION)
                activation_event_occurrence = create_event_occurrence(activation_offer)
                stock = create_stock_from_event_occurrence(activation_event_occurrence, price=0)
                booking = create_booking(user=user, stock=stock, venue=venue)
                repository.save(booking, user_offerer)
                user_id = user.id
                url = '/bookings/token/{}'.format(booking.token)

                # When
                response = TestClient(app.test_client()).with_auth('pro@email.fr').patch(url)

                # Then
                user = User.query.get(user_id)
                assert response.status_code == 204
                assert user.canBookFreeOffers is True
                assert user.deposits[0].amount == 500

    class Returns400:
        class WhenUserIsAnonymous:
            @clean_database
            def when_email_is_missing(self, app):
                # Given
                user = create_user()
                offerer = create_offerer()
                venue = create_venue(offerer)
                stock = create_stock_with_event_offer(offerer, venue, price=0)
                booking = create_booking(user=user, stock=stock, venue=venue)
                repository.save(booking)
                url = '/bookings/token/{}?&offer_id={}'.format(booking.token,
                                                               humanize(stock.resolvedOffer.id))

                # When
                response = TestClient(app.test_client()).patch(url)

                # Then
                assert response.status_code == 400
                assert response.json['email'] == [
                    "L'adresse email qui a servie à la réservation est obligatoire dans l'URL [?email=<email>]"]

            @clean_database
            def when_offer_id_is_missing(self, app):
                # Given
                user = create_user()
                offerer = create_offerer()
                venue = create_venue(offerer)
                stock = create_stock_with_event_offer(offerer, venue, price=0)
                booking = create_booking(user=user, stock=stock, venue=venue)
                repository.save(booking)
                url = '/bookings/token/{}?email={}'.format(booking.token, user.email)

                # When
                response = TestClient(app.test_client()).patch(url)

                # Then
                assert response.status_code == 400
                assert response.json['offer_id'] == [
                    "L'id de l'offre réservée est obligatoire dans l'URL [?offer_id=<id>]"]

            @clean_database
            def when_both_email_and_offer_id_are_missing(self, app):
                # Given
                user = create_user()
                offerer = create_offerer()
                venue = create_venue(offerer)
                stock = create_stock_with_event_offer(offerer, venue, price=0)
                booking = create_booking(user=user, stock=stock, venue=venue)
                repository.save(booking)
                url = '/bookings/token/{}'.format(booking.token, user.email)

                # When
                response = TestClient(app.test_client()).patch(url)

                # Then
                assert response.status_code == 400
                assert response.json['offer_id'] == [
                    "L'id de l'offre réservée est obligatoire dans l'URL [?offer_id=<id>]"]
                assert response.json['email'] == [
                    "L'adresse email qui a servie à la réservation est obligatoire dans l'URL [?email=<email>]"]

            @clean_database
            def when_there_is_not_enough_available_stock_to_validate_a_booking(self, app):
                # Given
                user = create_user()
                offerer = create_offerer()
                venue = create_venue(offerer)
                stock = create_stock_with_event_offer(offerer, venue, price=0)
                booking = create_booking(user=user, stock=stock, venue=venue)
                repository.save(booking)
                url = '/bookings/token/{}?email={}&offer_id={}'.format(booking.token, user.email,
                                                                       humanize(stock.resolvedOffer.id))

                stock.available = 0
                repository.save(stock)

                # When
                response = TestClient(app.test_client()).patch(url)

                # Then
                assert response.status_code == 400
                assert response.json['global'] == ["La quantité disponible pour cette offre est atteinte."]

    class Returns403:
        class WhenUserIsLoggedIn:
            @clean_database
            def when_user_is_not_attached_to_linked_offerer(self, app):
                # Given
                user = create_user()
                admin_user = create_user(email='admin@email.fr')
                offerer = create_offerer()
                venue = create_venue(offerer)
                stock = create_stock_with_event_offer(offerer, venue, price=0)
                booking = create_booking(user=user, stock=stock, venue=venue)
                repository.save(booking, admin_user)
                booking_id = booking.id
                url = '/bookings/token/{}?email={}'.format(booking.token, user.email)

                # When
                response = TestClient(app.test_client()).with_auth('admin@email.fr').patch(url)

                # Then
                assert response.status_code == 403
                assert response.json['global'] == ["Vous n'avez pas les droits d'accès suffisant pour accéder à cette information."]
                assert Booking.query.get(booking_id).isUsed is False

            @clean_database
            def when_user_is_not_admin_and_tries_to_patch_activation_offer(self, app):
                # Given
                user = create_user()
                pro_user = create_user(email='pro@email.fr', is_admin=False)
                offerer = create_offerer()
                user_offerer = create_user_offerer(pro_user, offerer)
                venue = create_venue(offerer)
                activation_offer = create_offer_with_event_product(venue, event_type=EventType.ACTIVATION)
                activation_event_occurrence = create_event_occurrence(activation_offer)
                stock = create_stock_from_event_occurrence(activation_event_occurrence, price=0)
                booking = create_booking(user=user, stock=stock, venue=venue)
                repository.save(booking, user_offerer)
                url = '/bookings/token/{}'.format(booking.token)

                # When
                response = TestClient(app.test_client()).with_auth('pro@email.fr').patch(url)

                # Then
                assert response.status_code == 403

    class Returns404:
        class WhenUserIsAnonymous:
            @clean_database
            def when_booking_does_not_exist(self, app):
                # Given
                user = create_user()
                offerer = create_offerer()
                venue = create_venue(offerer)
                stock = create_stock_with_event_offer(offerer, venue, price=0)
                booking = create_booking(user=user, stock=stock, venue=venue)
                repository.save(booking)
                url = '/bookings/token/{}?email={}&offer_id={}'.format(booking.token, 'wrong.email@test.com',
                                                                       humanize(stock.resolvedOffer.id))

                # When
                response = TestClient(app.test_client()).patch(url)

                # Then
                assert response.status_code == 404
                assert response.json['global'] == ["Cette contremarque n'a pas été trouvée"]

        class WhenUserIsLoggedIn:
            @clean_database
            def when_user_is_not_editor_and_email_does_not_match(self, app):
                # Given
                user = create_user()
                admin_user = create_user(email='admin@email.fr')
                offerer = create_offerer()
                venue = create_venue(offerer)
                stock = create_stock_with_event_offer(offerer, venue, price=0)
                booking = create_booking(user=user, stock=stock, venue=venue)
                repository.save(booking, admin_user)
                booking_id = booking.id
                url = '/bookings/token/{}?email={}'.format(booking.token, 'wrong@email.fr')

                # When
                response = TestClient(app.test_client()).with_auth('admin@email.fr').patch(url)

                # Then
                assert response.status_code == 404
                assert Booking.query.get(booking_id).isUsed is False

            @clean_database
            def when_email_has_special_characters_but_is_not_url_encoded(self, app):
                # Given
                user = create_user(email='user+plus@email.fr')
                user_admin = create_user(email='admin@email.fr')
                offerer = create_offerer()
                user_offerer = create_user_offerer(user_admin, offerer, is_admin=True)
                venue = create_venue(offerer)
                offer = create_offer_with_event_product(venue, event_name='Event Name')
                event_occurrence = create_event_occurrence(offer)
                stock = create_stock_from_event_occurrence(event_occurrence, price=0)
                booking = create_booking(user=user, stock=stock, venue=venue)

                repository.save(user_offerer, booking)
                url = '/bookings/token/{}?email={}'.format(booking.token, user.email)

                # When
                response = TestClient(app.test_client()).with_auth('admin@email.fr').patch(url)
                # Then
                assert response.status_code == 404

            @clean_database
            def when_user_is_not_editor_and_offer_id_is_invalid(self, app):
                # Given
                user = create_user()
                admin_user = create_user(email='admin@email.fr')
                offerer = create_offerer()
                venue = create_venue(offerer)
                stock = create_stock_with_event_offer(offerer, venue, price=0)
                booking = create_booking(user=user, stock=stock, venue=venue)
                repository.save(booking, admin_user)
                booking_id = booking.id
                url = '/bookings/token/{}?email={}&offer_id={}'.format(booking.token, user.email,
                                                                       humanize(123))

                # When
                response = TestClient(app.test_client()).with_auth('admin@email.fr').patch(url)

                # Then
                assert response.status_code == 404
                assert Booking.query.get(booking_id).isUsed is False

    class Returns405:
        class WhenUserIsAdmin:
            @clean_database
            def expect_no_new_deposits_when_the_linked_user_has_been_already_activated(self, app):
                # Given
                user = create_user(can_book_free_offers=False, is_admin=False)
                pro_user = create_user(can_book_free_offers=False, email='pro@email.fr', is_admin=True)
                offerer = create_offerer()
                user_offerer = create_user_offerer(pro_user, offerer)
                venue = create_venue(offerer)
                activation_offer = create_offer_with_event_product(venue, event_type=EventType.ACTIVATION)
                activation_event_occurrence = create_event_occurrence(activation_offer)
                stock = create_stock_from_event_occurrence(activation_event_occurrence, price=0)
                booking = create_booking(user=user, stock=stock, venue=venue)
                deposit = create_deposit(user, amount=500)
                repository.save(booking, user_offerer, deposit)
                user_id = user.id
                url = '/bookings/token/{}'.format(booking.token)

                # When
                response = TestClient(app.test_client()).with_auth('pro@email.fr').patch(url)

                # Then
                deposits_for_user = Deposit.query.filter_by(userId=user_id).all()
                assert response.status_code == 405
                assert len(deposits_for_user) == 1
                assert deposits_for_user[0].amount == 500

    class Returns410:
        class WhenUserIsLoggedIn:
            @clean_database
            def when_booking_has_been_cancelled_already(self, app):
                # Given
                user = create_user()
                admin_user = create_user(email='admin@email.fr')
                offerer = create_offerer()
                user_offerer = create_user_offerer(admin_user, offerer)
                venue = create_venue(offerer)
                stock = create_stock_with_event_offer(offerer, venue, price=0)
                booking = create_booking(user=user, stock=stock, venue=venue)
                booking.isCancelled = True
                repository.save(booking, user_offerer)
                booking_id = booking.id
                url = '/bookings/token/{}'.format(booking.token)

                # When
                response = TestClient(app.test_client()).with_auth('admin@email.fr').patch(url)

                # Then
                assert response.status_code == 410
                assert response.json['booking'] == ['Cette réservation a été annulée']
                assert Booking.query.get(booking_id).isUsed is False

            @clean_database
            def when_booking_has_been_validated_already(self, app):
                # Given
                user = create_user()
                admin_user = create_user(email='admin@email.fr')
                offerer = create_offerer()
                user_offerer = create_user_offerer(admin_user, offerer)
                venue = create_venue(offerer)
                stock = create_stock_with_event_offer(offerer, venue, price=0)
                booking = create_booking(user=user, stock=stock, venue=venue)
                booking.isUsed = True
                repository.save(booking, user_offerer)
                booking_id = booking.id
                url = '/bookings/token/{}'.format(booking.token)

                # When
                response = TestClient(app.test_client()).with_auth('admin@email.fr').patch(url)

                # Then
                assert response.status_code == 410
                assert response.json['booking'] == ['Cette réservation a déjà été validée']
                assert Booking.query.get(booking_id).isUsed is True
