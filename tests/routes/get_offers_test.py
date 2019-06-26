""" routes offers tests """
import secrets
from datetime import datetime, timedelta

from models import PcObject, Venue, EventType, ThingType
from models.offer_type import ProductType
from tests.conftest import clean_database, TestClient
from tests.test_utils import create_offer_with_event_product, \
    create_offerer, \
    create_offer_with_thing_product, \
    create_user, \
    create_user_offerer, \
    create_venue, \
    create_stock_from_offer
from utils.human_ids import dehumanize, humanize


class Get:
    class Returns200:
        @clean_database
        def test_results_are_paginated_by_chunks_of_10(self, app):
            # Given
            user = create_user(email='user@test.com')
            create_offers_for(user, 20)

            # when
            response = TestClient(app.test_client()).with_auth(email='user@test.com').get('/offers')

            # then
            offers = response.json
            assert response.status_code == 200
            assert len(offers) == 10

        @clean_database
        def test_results_are_paginated_by_default_on_page_1(self, app):
            # given
            user = create_user(email='user@test.com')
            create_offers_for(user, 20)
            auth_request = TestClient(app.test_client()).with_auth(email='user@test.com')
            offers = auth_request.get('/offers').json
            first_id = dehumanize(offers[0]['id'])

            # when
            response = auth_request.get('/offers?page=1')

            # then
            result = response.json
            assert response.status_code == 200
            assert dehumanize(result[0]['id']) == first_id

        @clean_database
        def test_returns_offers_sorted_by_id_desc(self, app):
            # given
            user = create_user(email='user@test.com')
            create_offers_for(user, 20)
            auth_request = TestClient(app.test_client()).with_auth(email='user@test.com')
            response_1 = auth_request.get('/offers?page=1')

            # when
            response_2 = auth_request.get('/offers?page=2')

            # then
            offers_1 = response_1.json
            offers_2 = response_2.json
            assert offers_1[-1]['dateCreated'] > offers_2[0]['dateCreated']

        @clean_database
        def test_results_are_sorted_by_id_desc_with_order_by_in_params(self, app):
            # given
            user = create_user(email='user@test.com')
            create_offers_for(user, 20)
            auth_request = TestClient(app.test_client()).with_auth(email='user@test.com')
            first_page_response = auth_request.get('/offers?page=1')

            # when
            second_page_response = auth_request.get('/offers?page=2&orderBy=offer.id%20desc')

            # then
            first_page_offers = first_page_response.json
            second_page_offers = second_page_response.json
            assert first_page_offers[-1]['dateCreated'] > second_page_offers[0]['dateCreated']

        @clean_database
        def test_results_are_filtered_by_given_venue_id(self, app):
            # given
            user = create_user(email='user@test.com')
            create_offers_for(user, 20, siren='123456789')
            create_offers_for(user, 20, siren='987654321')
            auth_request = TestClient(app.test_client()).with_auth(email='user@test.com')
            venue_id = Venue.query.first().id

            # when
            response = auth_request.get('/offers?venueId=' + humanize(venue_id))

            # then
            offers = response.json
            assert response.status_code == 200
            for offer in offers:
                assert offer['venueId'] == humanize(venue_id)

        @clean_database
        def test_can_be_filtered_and_paginated_at_the_same_time(self, app):
            # given
            user = create_user(email='user@test.com')
            create_offers_for(user, 20, siren='987654321')
            auth_request = TestClient(app.test_client()).with_auth(email='user@test.com')
            venue_id = Venue.query.first().id

            # when
            response = auth_request.get('/offers?venueId=' + humanize(venue_id) + '&page=2')

            # then
            offers = response.json
            assert response.status_code == 200
            for offer in offers:
                assert offer['venueId'] == humanize(venue_id)

        @clean_database
        def test_can_be_searched_and_filtered_and_paginated_at_the_same_time(self, app):
            # given
            user = create_user(email='user@test.com')
            create_offers_for(user, 20, siren='987654321')
            auth_request = TestClient(app.test_client()).with_auth(email='user@test.com')
            venue_id = Venue.query.first().id

            # when
            response = auth_request.get('/offers?venueId=' + humanize(venue_id) + '&page=1&keywords=Event')

            # then
            offers = response.json
            assert response.status_code == 200
            assert len(offers) == 10
            for offer in offers:
                assert offer['venueId'] == humanize(venue_id)
                assert 'event' in offer['name'].lower()
                assert 'event' in offer['product']['name'].lower()

        @clean_database
        def test_can_be_searched_using_multiple_search_terms(self, app):
            # given
            user = create_user(email='user@test.com')
            create_offers_for(user, 20, siren='987654321')
            auth_request = TestClient(app.test_client()).with_auth(email='user@test.com')
            venue_id = Venue.query.first().id

            # when
            response = auth_request.get(
                '/offers?venueId=' + humanize(venue_id) + '&page=1&search=Event Offer')

            # then
            offers = response.json
            assert response.status_code == 200
            assert len(offers) == 10
            assert len([o for o in offers if ProductType.is_event(o['type'])]) > 0
            assert len([o for o in offers if ProductType.is_thing(o['type'])]) > 0

        @clean_database
        def test_list_activation_offers_returns_offers_of_event_type(self, app):
            # given
            user = create_user()
            PcObject.save(user)
            auth_request = TestClient(app.test_client()).with_auth(email=user.email)
            now = datetime.utcnow()
            five_days_ago = now - timedelta(days=5)
            next_week = now + timedelta(days=7)
            offerer = create_offerer()
            venue1 = create_venue(offerer, siret=offerer.siren + '12345', postal_code='93000', departement_code='93')
            venue2 = create_venue(offerer, siret=offerer.siren + '67890', postal_code='93000', departement_code='93')
            venue3 = create_venue(offerer, siret=offerer.siren + '54321', postal_code='93000', departement_code='93')
            offer1 = create_offer_with_event_product(venue1, event_type=EventType.ACTIVATION)
            offer2 = create_offer_with_event_product(venue2, event_type=EventType.ACTIVATION)
            offer3 = create_offer_with_event_product(venue3, event_type=EventType.ACTIVATION)
            stock1 = create_stock_from_offer(offer1, price=0, booking_limit_datetime=five_days_ago)
            stock2 = create_stock_from_offer(offer2, price=0, booking_limit_datetime=next_week)
            stock3 = create_stock_from_offer(offer3, price=0, booking_limit_datetime=None)
            PcObject.save(stock1, stock2, stock3)

            # when
            response = auth_request.get('/offers/activation')

            # then
            json = response.json
            event_ids = [info['productId'] for info in json if ProductType.is_event(info['type'])]
            assert len(json) == 2
            assert response.status_code == 200
            assert humanize(offer2.productId) in event_ids
            assert humanize(offer3.productId) in event_ids

        @clean_database
        def test_returns_list_of_offers_with_thing_or_event_with_type_details(self, app):
            # given
            user = create_user(can_book_free_offers=False, is_admin=True)
            offerer = create_offerer()
            venue = create_venue(offerer, siret=offerer.siren + '12345', postal_code='93000', departement_code='93')
            event_offer = create_offer_with_event_product(venue, event_type=EventType.SPECTACLE_VIVANT)
            thing_offer = create_offer_with_thing_product(venue, thing_type=ThingType.LIVRE_EDITION)
            stock_event = create_stock_from_offer(event_offer, price=0)
            stock_thing = create_stock_from_offer(thing_offer, price=0)
            PcObject.save(user, stock_event, stock_thing)

            expected_thing_type = {
                'conditionalFields': ["author", "isbn"],
                'proLabel': "Livre - format papier ou numérique, abonnements lecture",
                'appLabel': 'Livres, cartes bibliothèque ou médiathèque',
                'offlineOnly': False,
                'onlineOnly': False,
                'sublabel': "Lire",
                'description': "S’abonner à un quotidien d’actualité ? À un hebdomadaire humoristique ? À un mensuel dédié à la nature ? Acheter une BD ou un manga ? Ou tout simplement ce livre dont tout le monde parle ?",
                'type': 'Thing',
                'value': 'ThingType.LIVRE_EDITION'
            }
            expected_event_type = {
                'conditionalFields': ["author", "showType", "stageDirector", "performer"],
                'proLabel': "Spectacle vivant",
                'appLabel': "Spectacle vivant",
                'offlineOnly': True,
                'onlineOnly': False,
                'sublabel': "Applaudir",
                'description': "Suivre un géant de 12 mètres dans la ville ? Rire aux éclats devant un stand up ? Rêver le temps d’un opéra ou d’un spectacle de danse ? Assister à une pièce de théâtre, ou se laisser conter une histoire ?",
                'type': 'Event',
                'value': 'EventType.SPECTACLE_VIVANT'
            }

            auth_request = TestClient(app.test_client()).with_auth(email=user.email)

            # when
            response = auth_request.get('/offers')

            # then
            json = response.json
            types = list(map(lambda x: x['product']['offerType'], json))
            thing_or_event_keys = list(map(lambda x: x['product'].keys(), json))
            assert response.status_code == 200
            assert expected_thing_type in types
            assert expected_event_type in types
            assert "type" not in thing_or_event_keys

        @clean_database
        def test_does_not_show_anything_to_user_offerer_when_not_validated(self, app):
            # Given
            user = create_user()
            offerer = create_offerer()
            venue = create_venue(offerer)
            user_offerer = create_user_offerer(user, offerer, validation_token=secrets.token_urlsafe(20))
            offer = create_offer_with_thing_product(venue)
            PcObject.save(user_offerer, offer)
            auth_request = TestClient(app.test_client()).with_auth(email=user.email)
            # When
            response = auth_request.get('/offers')

            # Then
            assert response.status_code == 200
            assert response.json == []


def create_offers_for(user, n, siren='123456789'):
    offerer = create_offerer(siren=siren)
    user_offerer = create_user_offerer(user, offerer)
    venue = create_venue(offerer, siret=siren + '1345')
    offers = create_n_mixed_offers_with_same_venue(venue, n=n)

    PcObject.save(user_offerer)
    PcObject.save(*offers)


def create_n_mixed_offers_with_same_venue(venue, n=10):
    offers = []
    for i in range(n // 2, 0, -1):
        date_created = datetime.utcnow() - timedelta(days=i)
        offers.append(
            create_offer_with_thing_product(venue, date_created=date_created, thing_name='Thing Offer %s' % i))
        offers.append(
            create_offer_with_event_product(venue, event_name='Event Offer %s' % i, date_created=date_created))
    return offers
