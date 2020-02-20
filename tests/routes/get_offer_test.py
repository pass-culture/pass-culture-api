from repository import repository
from tests.conftest import TestClient, clean_database
from tests.model_creators.generic_creators import create_user, create_stock, create_offerer, create_venue, \
    create_mediation, \
    create_bank_information, create_booking
from tests.model_creators.specific_creators import create_offer_with_thing_product
from utils.human_ids import humanize


class Get:
    class Returns200:
        @clean_database
        def when_user_has_rights_on_managing_offerer(self, app):
            # Given
            user = create_user(email='user@test.com')
            offerer = create_offerer()
            venue = create_venue(offerer)
            offer = create_offer_with_thing_product(venue)
            stock = create_stock(offer=offer)
            create_bank_information(venue=venue, id_at_providers=venue.siret)
            create_bank_information(offerer=offerer, id_at_providers=offerer.siren)

            repository.save(user, stock)

            # when
            response = TestClient(app.test_client()).with_auth(email='user@test.com') \
                .get(f'/offers/{humanize(offer.id)}')

            # then
            response_json = response.json
            assert response.status_code == 200
            assert 'iban' in response_json['venue']
            assert 'bic' in response_json['venue']
            assert 'iban' in response_json['venue']['managingOfferer']
            assert 'bic' in response_json['venue']['managingOfferer']
            assert 'validationToken' not in response_json['venue']['managingOfferer']

        @clean_database
        def when_returns_an_active_mediation(self, app):
            # Given
            user = create_user(email='user@test.com')
            offerer = create_offerer()
            venue = create_venue(offerer)
            offer = create_offer_with_thing_product(venue)
            mediation = create_mediation(offer, is_active=True)
            repository.save(user, mediation)

            # when
            response = TestClient(app.test_client()).with_auth(email='user@test.com') \
                .get(f'/offers/{humanize(offer.id)}')

            # then
            assert response.status_code == 200
            assert response.json['activeMediation'] is not None

        @clean_database
        def test_should_not_return_bookings(self, app):
            # Given
            user = create_user(email='user@example.com')
            beneficiary1 = create_user(email='jeune1@example.com')
            beneficiary2 = create_user(email='jeune2@example.com')
            offerer = create_offerer()
            venue = create_venue(offerer)
            offer = create_offer_with_thing_product(venue)
            stock = create_stock(offer=offer, price=0)
            booking1 = create_booking(user, stock=stock)
            booking2 = create_booking(beneficiary1, stock=stock)
            booking3 = create_booking(beneficiary2, stock=stock)
            repository.save(booking1, booking2, booking3)

            # when
            response = TestClient(app.test_client()).with_auth(email=user.email) \
                .get(f'/offers/{humanize(offer.id)}')

            # then
            assert response.status_code == 200
            assert 'bookings' not in response.json['stocks'][0]
