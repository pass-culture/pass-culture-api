from sqlalchemy_api_handler import ApiHandler, humanize

from models import Mediation
from tests.conftest import clean_database, TestClient
from tests.test_utils import create_user, \
    create_offer_with_event_product, \
    create_mediation, \
    create_offerer, \
    create_user_offerer, \
    create_venue


class Patch:
    class Returns200:
        @clean_database
        def when_mediation_is_edited(self, app):
            # given
            user = create_user()
            offerer = create_offerer()
            venue = create_venue(offerer)
            offer = create_offer_with_event_product(venue)
            user_offerer = create_user_offerer(user, offerer)
            mediation = create_mediation(offer)
            ApiHandler.save(mediation)
            ApiHandler.save(user, venue, offerer, user_offerer)
            mediation_id = mediation.id
            auth_request = TestClient(app.test_client()).with_auth(email=user.email)
            data = {'frontText': 'new front text', 'backText': 'new back text', 'isActive': False}

            # when
            response = auth_request.patch('/mediations/%s' % humanize(mediation.id), json=data)

            # then
            mediation = Mediation.query.get(mediation_id)
            assert response.status_code == 200
            assert response.json['id'] == humanize(mediation.id)
            assert response.json['frontText'] == mediation.frontText
            assert response.json['backText'] == mediation.backText
            assert response.json['isActive'] == mediation.isActive
            assert response.json['thumbUrl'] == mediation.thumbUrl
            assert mediation.isActive == data['isActive']
            assert mediation.frontText == data['frontText']
            assert mediation.backText == data['backText']


    class Returns403:
        @clean_database
        def when_current_user_is_not_attached_to_offerer_of_mediation(self, app):
            # given
            current_user = create_user(email='bobby@test.com')
            other_user = create_user(email='jimmy@test.com')
            offerer = create_offerer()
            venue = create_venue(offerer)
            offer = create_offer_with_event_product(venue)
            user_offerer = create_user_offerer(other_user, offerer)
            mediation = create_mediation(offer)
            ApiHandler.save(mediation)
            ApiHandler.save(other_user, current_user, venue, offerer, user_offerer)

            auth_request = TestClient(app.test_client()).with_auth(email=current_user.email)

            # when
            response = auth_request.patch('/mediations/%s' % humanize(mediation.id), json={})

            # then
            assert response.status_code == 403

    class Returns404:
        @clean_database
        def when_mediation_does_not_exist(self, app):
            # given
            user = create_user()
            ApiHandler.save(user)
            auth_request = TestClient(app.test_client()).with_auth(email=user.email)

            # when
            response = auth_request.patch('/mediations/ADFGA', json={})

            # then
            assert response.status_code == 404
