from sqlalchemy_api_handler import ApiHandler, as_dict

from models import Stock
from tests.conftest import clean_database
from tests.test_utils import create_user, create_offerer, create_user_offerer, create_product_with_event_type, \
    create_mediation, create_offer_with_event_product, create_venue, create_booking


class AsDictTest:
    @clean_database
    def test_returns_model_keys(self, app):
        # given
        user = create_user(postal_code=None)
        offerer = create_offerer()
        user_offerer = create_user_offerer(user, offerer)
        ApiHandler.save(user_offerer)
        USER_INCLUDES = []

        # when
        dict_result = as_dict(user, includes=USER_INCLUDES)

        # then
        assert 'publicName' in dict_result
        assert 'lastName' in dict_result
        assert 'firstName' in dict_result

    @clean_database
    def test_does_not_return_excluded_keys(self, app):
        # given
        user = create_user(postal_code=None)
        offerer = create_offerer()
        user_offerer = create_user_offerer(user, offerer)
        ApiHandler.save(user_offerer)
        USER_INCLUDES = ['-password', '-resetPasswordToken']

        # when
        dict_result = as_dict(user, includes=USER_INCLUDES)

        # then
        assert 'password' not in dict_result
        assert 'resetPasswordToken' not in dict_result

    @clean_database
    def test_does_not_return_properties_by_default(self, app):
        # given
        user = create_user(postal_code=None)
        offerer = create_offerer()
        user_offerer = create_user_offerer(user, offerer)
        ApiHandler.save(user_offerer)
        USER_INCLUDES = []

        # when
        dict_result = as_dict(user, includes=USER_INCLUDES)

        # then
        assert 'hasPhysicalVenues' not in dict_result
        assert 'hasOffers' not in dict_result

    @clean_database
    def test_returns_included_properties(self, app):
        # given
        user = create_user(postal_code=None)
        offerer = create_offerer()
        user_offerer = create_user_offerer(user, offerer)
        ApiHandler.save(user_offerer)
        USER_INCLUDES = ['hasPhysicalVenues', 'hasOffers']

        # when
        dict_result = as_dict(user, includes=USER_INCLUDES)

        # then
        assert 'hasPhysicalVenues' in dict_result
        assert 'hasOffers' in dict_result

    @clean_database
    def test_returns_model_keys_on_joined_relationships(self, app):
        # given
        user = create_user()
        offerer = create_offerer()
        user_offerer = create_user_offerer(user, offerer)
        ApiHandler.save(user_offerer)
        USER_INCLUDES = ['offerers']

        # when
        dict_result = as_dict(user, includes=USER_INCLUDES)

        # then
        assert 'offerers' in dict_result
        assert 'name' in dict_result['offerers'][0]
        assert 'siren' in dict_result['offerers'][0]

    @clean_database
    def test_returns_included_properties_on_joined_relationships(self, app):
        # given
        offerer = create_offerer()
        venue = create_venue(offerer)
        event_product = create_product_with_event_type(event_name='My Event')
        offer = create_offer_with_event_product(venue, product=event_product)
        mediation = create_mediation(offer)
        ApiHandler.save(mediation)
        EVENT_INCLUDES = [
            {
                "key": "mediations",
                "includes": ["thumbUrl"]
            }
        ]

        # when
        dict_result = as_dict(offer, includes=EVENT_INCLUDES)

        # then
        assert 'thumbUrl' in dict_result['mediations'][0]

    @clean_database
    def test_does_not_return_excluded_keys_on_joined_relationships(self, app):
        # given
        offerer = create_offerer()
        venue = create_venue(offerer)
        event_product = create_product_with_event_type(event_name='My Event')
        offer = create_offer_with_event_product(venue, product=event_product)
        mediation = create_mediation(offer)
        ApiHandler.save(mediation)
        EVENT_INCLUDES = [
            {
                "key": "mediations",
                "includes": ["-backText"]
            }
        ]

        # when
        dict_result = as_dict(offer, includes=EVENT_INCLUDES)

        # then
        assert 'backText' not in dict_result['mediations'][0]

    @clean_database
    def test_returns_humanized_ids_for_primary_keys(self, app):
        # given
        user = create_user(postal_code=None, idx=12)

        # when
        dict_result = as_dict(user, includes=[])

        # then
        assert dict_result['id'] == 'BQ'

    @clean_database
    def test_returns_humanized_ids_for_foreign_keys(self, app):
        # given
        user = create_user(postal_code=None, idx=12)
        booking = create_booking(user, Stock(), idx=13)
        booking.userId = user.id

        # when
        dict_result = as_dict(booking, includes=[])

        # then
        assert dict_result['userId'] == 'BQ'
