
import pytest

from models import PcObject
from tests.conftest import clean_database, TestClient
from tests.test_utils import create_venue,\
    create_offerer,\
    create_user,\
    create_user_offerer
from utils.human_ids import humanize


class Get:
    class Returns200:
        @clean_database
        def when_user_has_access_to_one_venue(self, app):
            # given
            offerer = create_offerer()
            venue_name = 'Theatre de la maison'
            venue = create_venue(offerer, name=('%s' % venue_name))
            user = create_user(email='user.pro@test.com')
            user_offerer = create_user_offerer(user, offerer)

            PcObject.save(user_offerer, venue)
            auth_request = TestClient(app.test_client()).with_auth(email=user.email)

            # when
            response = auth_request.get('/venues')

            # then
            assert response.status_code == 200
            assert len(response.json) == 1
            first_returned_venue = response.json[0]
            assert first_returned_venue['name'] == venue_name

        @clean_database
        def when_connected_does_not_return_unrelated_venues(self, app):
            # given
            theater_company = create_offerer(name='Shakespear company', siren='987654321')
            theater_administrator = create_user(email='user.pro@example.net')
            theater_user_offerer = create_user_offerer(theater_administrator, theater_company)
            theater_venue = create_venue(theater_company, name='National Shakespear Theater', siret='98765432112345')

            bookshop_offerer = create_offerer(name='Bookshop', siren='123456789')
            bookshop_user = create_user(email='bookshop.pro@example.net')
            bookshop_user_offerer = create_user_offerer(bookshop_user, bookshop_offerer)
            bookshop_venue = create_venue(bookshop_offerer, name='Contes et légendes', siret='12345678912345')

            PcObject.save(theater_user_offerer, theater_venue, bookshop_user_offerer, bookshop_venue)

            auth_request = TestClient(app.test_client()).with_auth(email=bookshop_user.email)

            # when
            response = auth_request.get('/venues')

            # then
            assert len(response.json) == 1
            first_returned_venue = response.json[0]
            assert first_returned_venue['name'] == 'Contes et légendes'

    class Returns403:
        @clean_database
        @pytest.mark.skip
        def when_current_user_doesnt_have_rights(self, app):
            # given
            offerer = create_offerer()
            user = create_user(email='user.pro@test.com')
            venue = create_venue(offerer, name='L\'encre et la plume')
            PcObject.save(user, venue)
            auth_request = TestClient(app.test_client()).with_auth(email=user.email)

            # when
            response = auth_request.get('/venues/%s' % humanize(venue.id))

            # then
            assert response.status_code == 403
            assert response.json['global'] == ["Cette structure n'est pas enregistrée chez cet utilisateur."]
