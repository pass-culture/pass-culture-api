from io import BytesIO
from sqlalchemy_api_handler import ApiHandler, humanize

from tests.conftest import clean_database, TestClient
from tests.files.images import ONE_PIXEL_PNG
from tests.test_utils import create_venue, create_offerer, create_user, \
    create_mediation, create_offer_with_event_product, create_user_offerer


class Post:
    class Returns200:
        @clean_database
        def when_a_file_is_uploaded_for_a_mediation(self, app):
            # given
            user = create_user()
            offerer = create_offerer()
            user_offerer = create_user_offerer(user, offerer)
            venue = create_venue(offerer)
            offer = create_offer_with_event_product(venue)
            mediation = create_mediation(offer)
            ApiHandler.save(user_offerer, mediation)

            auth_request = TestClient(app.test_client()).with_auth(email=user.email)

            # when
            response = auth_request.post(
                '/storage/thumb/%s/%s/%s' % ('mediations', humanize(mediation.id), '0'),
                files={'file': (BytesIO(ONE_PIXEL_PNG), '1.png')}
            )

            # then
            assert response.status_code == 200

    class Returns400:
        @clean_database
        def when_upload_is_not_authorized_on_model(self, app):
            # given
            user = create_user()
            offerer = create_offerer()
            venue = create_venue(offerer)
            ApiHandler.save(user, venue, offerer)

            auth_request = TestClient(app.test_client()).with_auth(email=user.email)

            # when
            response = auth_request.post(
                '/storage/thumb/%s/%s/%s' % ('venues', humanize(venue.id), '1'),
                files={'file': (BytesIO(b'123'), '1.png')}
            )

            # then
            assert response.status_code == 400
            assert response.json['text'] == 'upload is not authorized for this model'

    class Returns403:
        @clean_database
        def when_the_current_user_is_not_attached_to_the_offerers(self, app):
            # given
            user = create_user()
            offerer = create_offerer()
            venue = create_venue(offerer)
            offer = create_offer_with_event_product(venue)
            mediation = create_mediation(offer)
            ApiHandler.save(user, offer, mediation, venue, offerer)

            auth_request = TestClient(app.test_client()).with_auth(email=user.email)

            # when
            response = auth_request.post(
                '/storage/thumb/%s/%s/%s' % ('mediations', humanize(mediation.id), '0'),
                files={'file': (BytesIO(ONE_PIXEL_PNG), '1.png')}
            )

            # then
            assert response.status_code == 403
            assert response.json['global'] == ["Vous n'avez pas les droits d'accès suffisant pour accéder à cette information."]
