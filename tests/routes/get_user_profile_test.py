from datetime import datetime

from models import ThingType
from repository import repository
from tests.conftest import clean_database, TestClient
from tests.model_creators.generic_creators import create_booking, create_user, create_offerer, create_venue, \
    create_deposit, \
    create_user_offerer, create_recommendation
from tests.model_creators.specific_creators import create_stock_with_thing_offer, create_offer_with_thing_product


class Get:
    class Returns200:
        @clean_database
        def when_user_is_logged_in_and_has_no_deposit(self, app):
            # Given
            user = create_user(departement_code='93', email='toto@btmx.fr', public_name='Toto')
            repository.save(user)

            # When
            response = TestClient(app.test_client()) \
                .with_auth(email='toto@btmx.fr') \
                .get('/users/current')

            # Then
            assert response.status_code == 200
            json = response.json
            assert json['email'] == 'toto@btmx.fr'
            assert 'password' not in json
            assert 'clearTextPassword' not in json
            assert 'resetPasswordToken' not in json
            assert 'resetPasswordTokenValidityLimit' not in json

        @clean_database
        def test_returns_has_physical_venues_and_has_offers(self, app):
            # Given
            user = create_user(email='test@email.com')
            offerer = create_offerer()
            offerer2 = create_offerer(siren='123456788')
            user_offerer = create_user_offerer(user, offerer)
            user_offerer2 = create_user_offerer(user, offerer2)
            offerer_virtual_venue = create_venue(offerer, is_virtual=True, siret=None)
            offerer2_physical_venue = create_venue(offerer2, siret='12345678856734')
            offerer2_virtual_venue = create_venue(offerer, is_virtual=True, siret=None)
            offer = create_offer_with_thing_product(offerer_virtual_venue, thing_type=ThingType.JEUX_VIDEO_ABO, url='http://fake.url')
            offer2 = create_offer_with_thing_product(offerer2_physical_venue)

            repository.save(offer, offer2, offerer2_virtual_venue, user_offerer, user_offerer2)

            # When
            response = TestClient(app.test_client()).with_auth('test@email.com').get('/users/current')

            # Then
            assert response.json['hasPhysicalVenues'] is True
            assert response.json['hasOffers'] is True

    class Returns400:
        @clean_database
        def when_header_not_in_whitelist(self, app):
            # Given
            user = create_user(can_book_free_offers=True, email='e@mail.com', is_admin=False)
            repository.save(user)

            # When
            response = TestClient(app.test_client()) \
                .with_auth(email='e@mail.com') \
                .get('/users/current', headers={'origin': 'random.header.fr'})

            # Then
            assert response.status_code == 400
            assert response.json['global'] == ['Header non autorisé']

    class Returns401:
        @clean_database
        def when_user_is_not_logged_in(self, app):
            # When
            response = TestClient(app.test_client()).get('/users/current')

            # Then
            assert response.status_code == 401
