import pytest
from datetime import datetime, timedelta
from pprint import pprint

from models import PcObject
from models.db import db
from tests.conftest import clean_database, TestClient
from tests.test_utils import API_URL, \
    create_event_offer, \
    create_offerer, \
    create_recommendation, \
    create_user, \
    create_user_offerer, \
    create_venue, create_thing_offer, create_bank_information, create_stock
from utils.human_ids import humanize


@pytest.mark.standalone
class Patch:
    class Returns200:
        @clean_database
        def test_returns_200_and_expires_recos(self, app):
            # given
            user = create_user()
            offerer = create_offerer()
            venue = create_venue(offerer)
            offer = create_event_offer(venue)
            user_offerer = create_user_offerer(user, offerer)
            recommendation = create_recommendation(offer, user, valid_until_date=datetime.utcnow() + timedelta(days=7))
            PcObject.check_and_save(offer, user, venue, offerer, recommendation, user_offerer)

            auth_request = TestClient().with_auth(email=user.email)
            data = {'eventId': 'AE', 'isActive': False}

            # when
            response = auth_request.patch(API_URL + '/offers/%s' % humanize(offer.id), json=data)

            # then
            db.session.refresh(offer)
            assert response.status_code == 200
            assert response.json()['id'] == humanize(offer.id)
            assert response.json()['isActive'] == offer.isActive
            assert offer.isActive == data['isActive']
            # only isActive can be modified
            assert offer.eventId != data['eventId']
            assert response.json()['eventId'] != offer.eventId
            db.session.refresh(recommendation)
            assert recommendation.validUntilDate < datetime.utcnow()

    class Returns403:
        @clean_database
        def test_returns_403_if_user_is_not_attached_to_offerer_of_offer(self, app):
            # given
            current_user = create_user(email='bobby@test.com')
            other_user = create_user(email='jimmy@test.com')
            offerer = create_offerer()
            venue = create_venue(offerer)
            offer = create_event_offer(venue)
            user_offerer = create_user_offerer(other_user, offerer)
            PcObject.check_and_save(offer, other_user, current_user, venue, offerer, user_offerer)

            auth_request = TestClient().with_auth(email=current_user.email)

            # when
            response = auth_request.patch(API_URL + '/offers/%s' % humanize(offer.id), json={})

            # then
            error_message = response.json()
            assert response.status_code == 403
            assert error_message['global'] == ['Cette structure n\'est pas enregistrée chez cet utilisateur.']

    class Returns404:
        @clean_database
        def test_returns_404_if_offer_does_not_exist(self, app):
            # given
            user = create_user()
            PcObject.check_and_save(user)
            auth_request = TestClient().with_auth(email=user.email)

            # when
            response = auth_request.patch(API_URL + '/offers/ADFGA', json={})

            # then
            assert response.status_code == 404


@pytest.mark.standalone
class Get:
    class Returns200:
        @clean_database
        def when_user_has_rights_on_managing_offerer(self, app):
            # Given
            user = create_user(email='user@test.com')
            offerer = create_offerer()
            venue = create_venue(offerer)
            offer = create_thing_offer(venue)
            stock = create_stock(offer=offer)
            create_bank_information(venue=venue, id_at_providers=venue.siret)
            create_bank_information(offerer=offerer, id_at_providers=offerer.siren)

            PcObject.check_and_save(user, stock)

            # when
            response = TestClient().with_auth(email='user@test.com')\
                .get(API_URL + f'/offers/{humanize(offer.id)}')

            # then
            response_json = response.json()
            assert response.status_code == 200
            assert 'iban' in response_json['venue']
            assert 'bic' in response_json['venue']
            assert 'iban' in response_json['venue']['managingOfferer']
            assert 'bic' in response_json['venue']['managingOfferer']

