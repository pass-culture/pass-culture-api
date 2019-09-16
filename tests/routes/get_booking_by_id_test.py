from models import PcObject
from tests.conftest import clean_database, TestClient
from tests.test_utils import create_stock_with_thing_offer, \
    create_offer_with_thing_product, create_venue, create_offerer, \
    create_user, create_booking
from utils.human_ids import humanize


class Get:
    class Returns200:
        @clean_database
        def expect_booking_to_have_completed_url(self, app):
            # Given
            user = create_user(email='user+plus@email.fr')
            offerer = create_offerer()
            venue = create_venue(offerer)
            offer = create_offer_with_thing_product(venue,
                                                    url='https://host/path/{token}?offerId={offerId}&email={email}')
            stock = create_stock_with_thing_offer(offerer=offerer, venue=venue, offer=offer, price=0)
            booking = create_booking(user, stock, venue=venue, token='ABCDEF')

            PcObject.save(booking)

            # When
            response = TestClient(app.test_client()).with_auth(user.email).get(
                '/bookings/' + humanize(booking.id))

            # Then
            assert response.status_code == 200
            response_json = response.json
            assert response_json[
                       'completedUrl'] == 'https://host/path/ABCDEF?offerId=%s&email=user+plus@email.fr' % humanize(
                offer.id)
            assert 'stock' in response_json
            assert 'offer' in response_json['stock']
            assert 'venue' in response_json['stock']['offer']
            assert 'validationToken' not in response_json['stock']['offer']
