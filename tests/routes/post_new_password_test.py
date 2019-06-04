from datetime import datetime, timedelta

from models import PcObject
from models.db import db
from tests.conftest import clean_database, TestClient
from tests.test_utils import API_URL, create_user


class PostNewPassword:
    class Returns400:
        @clean_database
        def when_the_token_is_outdated(self, app):
            # given
            user = create_user(reset_password_token='KL89PBNG51',
                               reset_password_token_validity_limit=datetime.utcnow() - timedelta(days=2))
            PcObject.save(user)

            data = {
                'token': 'KL89PBNG51',
                'newPassword': 'N3W_p4ssw0rd'
            }

            # when
            response = TestClient().post(API_URL + '/users/new-password', json=data,
                                         headers={'origin': 'http://localhost:3000'})

            # then
            assert response.status_code == 400
            assert response.json()['token'] == [
                'Votre lien de changement de mot de passe est périmé. Veuillez effecture une nouvelle demande.'
            ]

        @clean_database
        def when_the_token_is_unknown(self, app):
            # given
            user = create_user(reset_password_token='KL89PBNG51')
            PcObject.save(user)

            data = {
                'token': 'AZER1QSDF2',
                'newPassword': 'N3W_p4ssw0rd'
            }

            # when
            response = TestClient().post(API_URL + '/users/new-password', json=data,
                                         headers={'origin': 'http://localhost:3000'})

            # then
            assert response.status_code == 400
            assert response.json()['token'] == [
                'Votre lien de changement de mot de passe est invalide.'
            ]

        @clean_database
        def when_the_token_is_missing(self, app):
            # given
            user = create_user(reset_password_token='KL89PBNG51')
            PcObject.save(user)

            data = {'newPassword': 'N3W_p4ssw0rd'}

            # when
            response = TestClient().post(API_URL + '/users/new-password', json=data,
                                         headers={'origin': 'http://localhost:3000'})

            # then
            assert response.status_code == 400
            assert response.json()['token'] == [
                'Votre lien de changement de mot de passe est invalide.'
            ]

        @clean_database
        def when_new_password_is_missing(self, app):
            # given
            user = create_user(reset_password_token='KL89PBNG51')
            PcObject.save(user)

            data = {'token': 'KL89PBNG51'}

            # when
            response = TestClient().post(API_URL + '/users/new-password', json=data,
                                         headers={'origin': 'http://localhost:3000'})

            # then
            assert response.status_code == 400
            assert response.json()['newPassword'] == [
                'Vous devez renseigner un nouveau mot de passe.'
            ]

        @clean_database
        def when_new_password_is_not_strong_enough(self, app):
            # given
            user = create_user(reset_password_token='KL89PBNG51')
            PcObject.save(user)

            data = {'token': 'KL89PBNG51', 'newPassword': 'weak_password'}

            # when
            response = TestClient().post(API_URL + '/users/new-password', json=data,
                                         headers={'origin': 'http://localhost:3000'})

            # then
            assert response.status_code == 400
            assert response.json()['newPassword'] == [
                'Le mot de passe doit faire au moins 12 caractères et contenir à minima '
                '1 majuscule, 1 minuscule, 1 chiffre et 1 caractère spécial parmi _-&?~#|^@=+.$,<>%*!:;'
            ]

    class Returns204:
        @clean_database
        def when_new_password_is_valid(self, app):
            # given
            user = create_user(reset_password_token='KL89PBNG51')
            PcObject.save(user)

            data = {
                'token': 'KL89PBNG51',
                'newPassword': 'N3W_p4ssw0rd'
            }

            # when
            response = TestClient().post(API_URL + '/users/new-password', json=data,
                                         headers={'origin': 'http://localhost:3000'})

            # then
            db.session.refresh(user)
            assert response.status_code == 204
            assert user.checkPassword('N3W_p4ssw0rd')
            assert user.resetPasswordToken is None
            assert user.resetPasswordTokenValidityLimit is None
