import secrets

from models import UserOfferer
from repository import repository
from tests.conftest import clean_database, TestClient
from tests.model_creators.generic_creators import create_user, create_offerer, create_user_offerer


class Get:
    class Returns202:
        @clean_database
        def expect_user_offerer_attachment_to_be_validated(self, app):
            # Given
            user_offerer_token = secrets.token_urlsafe(20)
            offerer_token = secrets.token_urlsafe(20)
            offerer = create_offerer(siren='349974931', address='12 boulevard de Pesaro', city='Nanterre', postal_code='92000', name='Crédit Coopératif',
                                     validation_token=offerer_token)
            user = create_user()
            user_offerer = create_user_offerer(user, offerer, validation_token=user_offerer_token)
            repository.save(offerer, user_offerer)
            user_offerer_id = offerer.id

            # When
            response = TestClient(app.test_client()).get('/validate/user-offerer/' + user_offerer_token,
                                                         headers={'origin': 'http://localhost:3000'})

            # Then
            assert response.status_code == 202

            user_offerer = UserOfferer.query \
                .filter_by(offererId=user_offerer_id) \
                .first()

            assert user_offerer.isValidated


    class Returns404:
        @clean_database
        def expect_user_offerer_attachment_not_to_be_validated_with_unknown_token(self, app):
            # when
            response = TestClient(app.test_client()).with_auth(email='bobby@example.net') \
                .get('/validate/user-offerer/123')

            # then
            assert response.status_code == 404


        @clean_database
        def expect_user_offerer_attachment_not_to_be_validated_with_same_token(self, app):
            user_offerer_token = secrets.token_urlsafe(20)
            offerer_token = secrets.token_urlsafe(20)

            offerer = create_offerer(siren='349974931', address='12 boulevard de Pesaro', city='Nanterre',
                                     postal_code='92000', name='Crédit Coopératif',
                                     validation_token=offerer_token)
            user = create_user()
            user_offerer = create_user_offerer(user, offerer, validation_token=user_offerer_token)
            repository.save(offerer, user_offerer)
            user_offerer_id = offerer.id


            # When
            TestClient(app.test_client()).get('/validate/user-offerer/' + user_offerer_token,
                                              headers={'origin': 'http://localhost:3000'})

            response = TestClient(app.test_client()).get('/validate/user-offerer/' + user_offerer_token,
                                                         headers={'origin': 'http://localhost:3000'})

            # Then
            assert response.status_code == 404
            user_offerer = UserOfferer.query \
                .filter_by(offererId=user_offerer_id) \
                .first()

            assert response.json['validation'][0] == "Aucun(e) objet ne correspond à ce code de validation ou l'objet est déjà validé"

            assert user_offerer.isValidated


