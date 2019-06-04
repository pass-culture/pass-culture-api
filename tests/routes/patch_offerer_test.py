""" routes offerer """
import pytest
from datetime import timedelta, datetime

from models import PcObject
from models.db import db
from models.pc_object import serialize
from tests.conftest import clean_database, TestClient
from tests.test_utils import API_URL, \
    create_offer_with_event_product, \
    create_offerer, \
    create_recommendation, \
    create_offer_with_thing_product, \
    create_user, \
    create_user_offerer, \
    create_venue
from utils.human_ids import humanize


class Patch:
    class Returns403:
        @clean_database
        def when_user_does_not_have_rights_on_offerer(self, app):
            # given
            user = create_user()
            offerer = create_offerer()
            user_offerer = create_user_offerer(user, offerer, is_admin=False)
            PcObject.save(user_offerer)
            body = {'isActive': False}

            # when
            response = TestClient() \
                .with_auth(user.email) \
                .patch(API_URL + '/offerers/%s' % humanize(offerer.id), json=body)

            # then
            assert response.status_code == 403

    class Returns400:
        @clean_database
        def when_editing_non_authorised_fields(self, app):
            # given
            user = create_user()
            offerer = create_offerer()
            user_offerer = create_user_offerer(user, offerer, is_admin=True)
            PcObject.save(user_offerer)
            body = {'thumbCount': 0, 'idAtProviders': 'zfeej',
                    'dateModifiedAtLastProvider': serialize(datetime(2016, 2, 1)), 'address': '123 nouvelle adresse',
                    'postalCode': '75001',
                    'city': 'Paris', 'validationToken': 'ozieghieof', 'id': humanize(10),
                    'dateCreated': serialize(datetime(2015, 2, 1)),
                    'name': 'Nouveau Nom', 'siren': '989807829', 'lastProviderId': humanize(1)}

            # when
            response = TestClient() \
                .with_auth(user.email) \
                .patch(API_URL + '/offerers/%s' % humanize(offerer.id), json=body)

            # then
            assert response.status_code == 400
            for key in body:
                assert response.json()[key] == ['Vous ne pouvez pas modifier ce champ']

    class Returns200:
        @clean_database
        def when_deactivating_offerer_and_expires_recos(self, app):
            # given
            user = create_user()
            other_user = create_user(email='other@email.fr')
            offerer = create_offerer(siren='987654321')
            other_offerer = create_offerer()
            venue1 = create_venue(offerer, siret=offerer.siren + '12345')
            venue2 = create_venue(offerer, siret=offerer.siren + '12346')
            other_venue = create_venue(other_offerer)
            offer_venue1_1 = create_offer_with_event_product(venue1)
            offer_venue2_1 = create_offer_with_event_product(venue2)
            offer_venue2_2 = create_offer_with_thing_product(venue2)
            other_offer = create_offer_with_event_product(other_venue)
            user_offerer = create_user_offerer(user, offerer, is_admin=True)
            original_validity_date = datetime.utcnow() + timedelta(days=7)
            recommendation1 = create_recommendation(offer_venue1_1, other_user, valid_until_date=original_validity_date)
            recommendation2 = create_recommendation(offer_venue2_1, other_user, valid_until_date=original_validity_date)
            recommendation3 = create_recommendation(offer_venue2_2, other_user, valid_until_date=original_validity_date)
            recommendation4 = create_recommendation(offer_venue2_2, user, valid_until_date=original_validity_date)
            other_recommendation = create_recommendation(other_offer, user, valid_until_date=original_validity_date)
            PcObject.save(recommendation1, recommendation2, recommendation3, recommendation4,
                          other_recommendation,
                          user_offerer)

            data = {'isActive': False}

            # when
            response = TestClient() \
                .with_auth(user.email) \
                .patch(API_URL + '/offerers/%s' % humanize(offerer.id), json=data)

            # then
            db.session.refresh(offerer)
            assert response.status_code == 200
            assert response.json()['isActive'] == offerer.isActive
            assert offerer.isActive == data['isActive']
            db.session.refresh(recommendation1)
            db.session.refresh(recommendation2)
            db.session.refresh(recommendation3)
            db.session.refresh(recommendation4)
            db.session.refresh(other_recommendation)
            assert recommendation1.validUntilDate < datetime.utcnow()
            assert recommendation2.validUntilDate < datetime.utcnow()
            assert recommendation3.validUntilDate < datetime.utcnow()
            assert recommendation4.validUntilDate < datetime.utcnow()
            assert other_recommendation.validUntilDate == original_validity_date
