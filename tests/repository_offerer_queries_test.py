import pytest
import secrets
from datetime import datetime, timedelta

from models import PcObject
from repository.offerer_queries import find_all_offerers_with_managing_user_information, \
    find_all_offerers_with_managing_user_information_and_venue, \
    find_all_offerers_with_managing_user_information_and_not_virtual_venue, \
    find_all_offerers_with_venue, find_first_by_user_offerer_id, find_all_pending_validation, \
    find_filtered_offerers
from repository.user_queries import find_all_emails_of_user_offerers_admins
from tests.conftest import clean_database
from tests.test_utils import create_user, create_offerer, create_user_offerer, create_venue, \
    create_event_offer, create_thing_offer, create_event_occurrence, \
    create_stock_with_thing_offer, create_stock_from_event_occurrence, create_bank_information


@pytest.mark.standalone
@clean_database
def test_find_all_emails_of_user_offerers_admins_returns_list_of_user_emails_having_user_offerer_with_admin_rights_on_offerer(
        app):
    # Given
    offerer = create_offerer()
    user_admin1 = create_user(email='admin1@offerer.com')
    user_admin2 = create_user(email='admin2@offerer.com')
    user_editor = create_user(email='editor@offerer.com')
    user_admin_not_validated = create_user(email='admin_not_validated@offerer.com')
    user_random = create_user(email='random@user.com')
    user_offerer_admin1 = create_user_offerer(user_admin1, offerer, is_admin=True)
    user_offerer_admin2 = create_user_offerer(user_admin2, offerer, is_admin=True)
    user_offerer_admin_not_validated = create_user_offerer(user_admin_not_validated, offerer,
                                                           validation_token=secrets.token_urlsafe(20), is_admin=True)
    user_offerer_editor = create_user_offerer(user_editor, offerer, is_admin=False)
    PcObject.check_and_save(user_random, user_offerer_admin1, user_offerer_admin2, user_offerer_admin_not_validated,
                            user_offerer_editor)

    # When
    emails = find_all_emails_of_user_offerers_admins(offerer.id)

    # Then
    assert set(emails) == {'admin1@offerer.com', 'admin2@offerer.com'}
    assert type(emails) == list


@pytest.mark.standalone
@clean_database
def test_find_all_offerers_with_managing_user_information(app):
    # given
    user_admin1 = create_user(email='admin1@offerer.com')
    user_admin2 = create_user(email='admin2@offerer.com')
    user_editor1 = create_user(email='editor1@offerer.com')
    offerer1 = create_offerer(name='offerer1')
    offerer2 = create_offerer(name='offerer2', siren='789456123')
    user_offerer1 = create_user_offerer(user_admin1, offerer1, is_admin=True)
    user_offerer2 = create_user_offerer(user_editor1, offerer1, is_admin=False)
    user_offerer3 = create_user_offerer(user_admin1, offerer2, is_admin=True)
    user_offerer4 = create_user_offerer(user_admin2, offerer2, is_admin=True)
    PcObject.check_and_save(user_admin1, user_admin2, user_editor1, offerer1, offerer2,
                            user_offerer1, user_offerer2, user_offerer3, user_offerer4)

    # when
    offerers = find_all_offerers_with_managing_user_information()

    # then
    assert len(offerers) == 4
    assert len(offerers[0]) == 10
    assert offerer1.siren in offerers[1].siren
    assert user_admin2.email in offerers[3].email


@pytest.mark.standalone
@clean_database
def test_find_all_offerers_with_managing_user_information_and_venue(app):
    # given
    user_admin1 = create_user(email='admin1@offerer.com')
    user_admin2 = create_user(email='admin2@offerer.com')
    user_editor1 = create_user(email='editor1@offerer.com')
    offerer1 = create_offerer(name='offerer1')
    offerer2 = create_offerer(name='offerer2', siren='789456123')
    venue1 = create_venue(offerer1, siret='123456789abcde')
    venue2 = create_venue(offerer2, siret='123456789abcdf')
    venue3 = create_venue(offerer2, siret='123456789abcdg', booking_email='test@test.test')
    user_offerer1 = create_user_offerer(user_admin1, offerer1, is_admin=True)
    user_offerer2 = create_user_offerer(user_editor1, offerer1, is_admin=False)
    user_offerer3 = create_user_offerer(user_admin1, offerer2, is_admin=True)
    user_offerer4 = create_user_offerer(user_admin2, offerer2, is_admin=True)
    PcObject.check_and_save(venue1, venue2, venue3, user_offerer1, user_offerer2, user_offerer3,
                            user_offerer4)

    # when
    offerers = find_all_offerers_with_managing_user_information_and_venue()

    # then
    assert len(offerers) == 6
    assert len(offerers[0]) == 13
    assert offerer1.city in offerers[0].city
    assert offerer2.siren == offerers[2].siren
    assert offerer2.siren == offerers[3].siren


@pytest.mark.standalone
@clean_database
def test_find_all_offerers_with_managing_user_information_and_not_virtual_venue(app):
    # given
    user_admin1 = create_user(email='admin1@offerer.com')
    user_admin2 = create_user(email='admin2@offerer.com')
    offerer1 = create_offerer(name='offerer1')
    offerer2 = create_offerer(name='offerer2', siren='789456123')
    venue1 = create_venue(offerer1, is_virtual=True, siret=None)
    venue2 = create_venue(offerer2, is_virtual=True, siret=None)
    venue3 = create_venue(offerer2, is_virtual=False)
    user_offerer1 = create_user_offerer(user_admin1, offerer1, is_admin=True)
    user_offerer3 = create_user_offerer(user_admin1, offerer2, is_admin=True)
    user_offerer4 = create_user_offerer(user_admin2, offerer2, is_admin=True)
    PcObject.check_and_save(venue1, venue2, venue3, user_offerer1, user_offerer3, user_offerer4)

    # when
    offerers = find_all_offerers_with_managing_user_information_and_not_virtual_venue()

    # then
    assert len(offerers) == 2
    assert len(offerers[0]) == 13
    assert user_admin1.email in offerers[0].email
    assert user_admin2.email in offerers[1].email
    assert offerer2.siren == offerers[1].siren


@pytest.mark.standalone
@clean_database
def test_find_all_offerers_with_venue(app):
    # given
    offerer1 = create_offerer(name='offerer1')
    offerer2 = create_offerer(name='offerer2', siren='789456123')
    venue1 = create_venue(offerer1, is_virtual=True, siret=None)
    venue2 = create_venue(offerer2, is_virtual=True, siret=None, booking_email='test@test.test')
    venue3 = create_venue(offerer2, is_virtual=False)
    PcObject.check_and_save(offerer1, offerer2, venue1, venue2, venue3)

    # when
    offerers = find_all_offerers_with_venue()

    # then
    assert len(offerers) == 3
    assert len(offerers[0]) == 7
    assert offerer1.id == offerers[0][0]
    assert venue2.bookingEmail in offerers[1].bookingEmail
    assert venue1.bookingEmail in offerers[0].bookingEmail


@pytest.mark.standalone
@clean_database
def test_get_all_pending_offerers_return_requested_tokens_in_case_only_venue_not_validated(app):
    # given
    user_validated = create_user(email="user@user.pro", can_book_free_offers=False, is_admin=False)
    offerer_validated = create_offerer()
    user_offerer_validated = create_user_offerer(user_validated, offerer_validated)
    venue_not_validated = create_venue(offerer_validated, siret=None, comment="comment because no siret",
                                       validation_token="venue_validation_token")
    PcObject.check_and_save(offerer_validated, user_offerer_validated, user_validated, venue_not_validated)

    # when
    offerers = find_all_pending_validation()

    offerer = offerers[0]
    user_offerer = offerer.UserOfferers[0]
    user = user_offerer.user
    venue = offerer.managedVenues[0]

    # then
    assert offerer.validationToken == offerer_validated.validationToken
    assert user_offerer.validationToken == user_offerer_validated.validationToken
    assert user.validationToken == user_validated.validationToken
    assert venue.validationToken == venue_not_validated.validationToken


@pytest.mark.standalone
@clean_database
def test_get_all_pending_offerers_return_requested_tokens_in_case_only_user_not_validated(app):
    # given
    user_not_validated = create_user(email="user@user.pro", can_book_free_offers=False, is_admin=False,
                                     validation_token="token_for_user")
    offerer_validated = create_offerer()
    user_offerer_validated = create_user_offerer(user_not_validated, offerer_validated)
    venue_validated = create_venue(offerer_validated)
    PcObject.check_and_save(offerer_validated, user_offerer_validated, user_not_validated, venue_validated)

    # when
    offerers = find_all_pending_validation()

    offerer = offerers[0]
    user_offerer = offerer.UserOfferers[0]
    user = user_offerer.user
    venue = offerer.managedVenues[0]

    # then
    assert offerer.validationToken == offerer_validated.validationToken
    assert user_offerer.validationToken == user_offerer_validated.validationToken
    assert user.validationToken == user_not_validated.validationToken
    assert venue.validationToken == venue_validated.validationToken


@pytest.mark.standalone
@clean_database
def test_get_all_pending_offerers_return_requested_tokens_in_case_only_user_offerer_not_validated(app):
    # given
    user_validated = create_user(email="user@user.pro", can_book_free_offers=False, is_admin=False)
    offerer_validated = create_offerer()
    user_offerer_not_validated = create_user_offerer(user_validated, offerer_validated,
                                                     validation_token='user_off_token')
    venue_validated = create_venue(offerer_validated)
    PcObject.check_and_save(offerer_validated, user_offerer_not_validated, user_validated, venue_validated)

    # when
    offerers = find_all_pending_validation()

    offerer = offerers[0]
    user_offerer = offerer.UserOfferers[0]
    user = user_offerer.user
    venue = offerer.managedVenues[0]

    # then
    assert offerer.validationToken == offerer_validated.validationToken
    assert user_offerer.validationToken == user_offerer_not_validated.validationToken
    assert user.validationToken == user_validated.validationToken
    assert venue.validationToken == venue_validated.validationToken


@pytest.mark.standalone
@clean_database
def test_get_all_pending_offerers_return_nothing_in_case_only_offerer_not_validated(app):
    # given
    user_validated = create_user(email="user@user.pro", can_book_free_offers=False, is_admin=False)
    offerer_not_validated = create_offerer(validation_token="this_offerer_has_a_token")
    user_offerer_validated = create_user_offerer(user_validated, offerer_not_validated)
    venue_validated = create_venue(offerer_not_validated)
    PcObject.check_and_save(offerer_not_validated, user_offerer_validated, user_validated, venue_validated)

    # when
    offerers = find_all_pending_validation()

    offerer = offerers[0]
    user_offerer = offerer.UserOfferers[0]
    user = user_offerer.user
    venue = offerer.managedVenues[0]

    # then
    assert offerer.validationToken == offerer_not_validated.validationToken
    assert user_offerer.validationToken == user_offerer_validated.validationToken
    assert user.validationToken == user_validated.validationToken
    assert venue.validationToken == venue_validated.validationToken


@pytest.mark.standalone
@clean_database
def test_get_all_pending_offerers_return_empty_list_in_case_all_validated(app):
    # given
    user_validated = create_user(email="user@user.pro", can_book_free_offers=False, is_admin=False)
    offerer_validated = create_offerer()
    user_offerer_validated = create_user_offerer(user_validated, offerer_validated)
    venue_validated = create_venue(offerer_validated)
    PcObject.check_and_save(offerer_validated, user_offerer_validated, user_validated, venue_validated)

    # when
    offerers = find_all_pending_validation()
    # then
    assert offerers == []


@pytest.mark.standalone
@clean_database
def test_find_first_by_user_offerer_id_returns_the_first_offerer_that_was_created(app):
    # given
    user = create_user()
    offerer1 = create_offerer(name='offerer1', siren='123456789')
    offerer2 = create_offerer(name='offerer2', siren='789456123')
    offerer3 = create_offerer(name='offerer2', siren='987654321')
    user_offerer1 = create_user_offerer(user, offerer1)
    user_offerer2 = create_user_offerer(user, offerer2)
    PcObject.check_and_save(user_offerer1, user_offerer2, offerer3)

    # when
    offerer = find_first_by_user_offerer_id(user_offerer1.id)

    # then
    assert offerer.id == offerer1.id


@pytest.mark.standalone
@clean_database
def test_find_filtered_offerers_with_sirens_params_return_filtered_offerers(app):
    # given
    offerer_123456789 = create_offerer(name="offerer_123456789", siren="123456789")
    offerer_123456781 = create_offerer(name="offerer_123456781", siren="123456781")
    offerer_123456782 = create_offerer(name="offerer_123456782", siren="123456782")
    offerer_123456783 = create_offerer(name="offerer_123456783", siren="123456783")
    offerer_123456784 = create_offerer(name="offerer_123456784", siren="123456784")

    PcObject.check_and_save(offerer_123456789, offerer_123456781, offerer_123456782,
                            offerer_123456783, offerer_123456784)

    # when
    query_with_sirens = find_filtered_offerers(sirens=["123456781", "123456782", "123456783"])

    # then
    assert offerer_123456789 not in query_with_sirens
    assert offerer_123456781 in query_with_sirens
    assert offerer_123456782 in query_with_sirens
    assert offerer_123456783 in query_with_sirens
    assert offerer_123456784 not in query_with_sirens


@pytest.mark.standalone
@clean_database
def test_find_filtered_offerers_with_dpts_param_return_filtered_offerers(app):
    # Given
    offerer_93 = create_offerer(postal_code="93125")
    offerer_67 = create_offerer(postal_code="67000", siren="123456781")
    offerer_34 = create_offerer(postal_code="34758", siren="123456782")
    offerer_00 = create_offerer(postal_code="00930", siren="123456783")
    offerer_01 = create_offerer(postal_code="00793", siren="123456784")
    offerer_78 = create_offerer(postal_code="78758", siren="123456785")
    offerer_973 = create_offerer(postal_code="97393", siren="123456786")
    offerer_2A = create_offerer(postal_code="2A793", siren="123456787")

    PcObject.check_and_save(offerer_93, offerer_67, offerer_34, offerer_00, offerer_01, offerer_78,
                            offerer_973, offerer_2A)

    # When
    query_with_dpts = find_filtered_offerers(dpts=['93', '67', '2A', '973'])

    # Then
    assert offerer_93 in query_with_dpts
    assert offerer_67 in query_with_dpts
    assert offerer_34 not in query_with_dpts
    assert offerer_00 not in query_with_dpts
    assert offerer_01 not in query_with_dpts
    assert offerer_78 not in query_with_dpts
    assert offerer_973 in query_with_dpts
    assert offerer_2A in query_with_dpts


@pytest.mark.standalone
@clean_database
def test_find_filtered_offerers_with_zipcodes_param_return_filtered_offerers(app):
    # Given
    offerer_93125 = create_offerer(postal_code="93125")
    offerer_67000 = create_offerer(postal_code="67000", siren="123456781")
    offerer_34758 = create_offerer(postal_code="34758", siren="123456782")

    PcObject.check_and_save(offerer_93125, offerer_67000, offerer_34758)

    # When
    query_with_zipcodes = find_filtered_offerers(zip_codes=['93125', '34758'])

    # Then
    assert offerer_93125 in query_with_zipcodes
    assert offerer_67000 not in query_with_zipcodes
    assert offerer_34758 in query_with_zipcodes


@pytest.mark.standalone
@clean_database
def test_find_filtered_offerers_with_date_params_return_filtered_offerers(app):
    # Given
    offerer_in_date_range = create_offerer(siren="123456781", date_created=datetime(2018, 7, 15))
    offerer_20180701 = create_offerer(siren="123456782", date_created=datetime(2018, 7, 1))
    offerer_20180801 = create_offerer(siren="123456783", date_created=datetime(2018, 8, 1))
    offerer_before_date_range = create_offerer(siren="123456784", date_created=datetime(2017, 7, 15))
    offerer_after_date_range = create_offerer(siren="123456785", date_created=datetime(2018, 12, 15))

    PcObject.check_and_save(offerer_in_date_range, offerer_20180701, offerer_20180801,
                            offerer_before_date_range, offerer_after_date_range)

    # When
    query_with_date = find_filtered_offerers(from_date='2018-07-01',
                                             to_date='2018-08-01')

    # Then
    assert offerer_in_date_range in query_with_date
    assert offerer_20180701 in query_with_date
    assert offerer_20180801 in query_with_date
    assert offerer_before_date_range not in query_with_date
    assert offerer_after_date_range not in query_with_date


@pytest.mark.standalone
@clean_database
def test_find_filtered_offerers_with_has_siren_param_return_filtered_offerers(app):
    # Given
    offerer_with_siren = create_offerer(siren="123456789")
    offerer_without_siren = create_offerer(siren=None)

    PcObject.check_and_save(offerer_with_siren, offerer_without_siren)

    # When
    query_no_siren = find_filtered_offerers(has_siren=False)

    # Then
    assert offerer_with_siren not in query_no_siren
    assert offerer_without_siren in query_no_siren


@pytest.mark.standalone
@clean_database
def test_find_filtered_offerers_with_is_validated_param_return_filtered_offerers(app):
    # Given
    offerer_validated = create_offerer(siren="123456789", validation_token=None)
    offerer_not_validated = create_offerer(siren="123456781", validation_token="a_token")

    PcObject.check_and_save(offerer_validated, offerer_not_validated)

    # When
    query_only_validated = find_filtered_offerers(is_validated=True)

    # Then
    assert offerer_validated in query_only_validated
    assert offerer_not_validated not in query_only_validated


@pytest.mark.standalone
@clean_database
def test_find_filtered_offerers_with_is_active_param_return_filtered_offerers(app):
    # Given
    offerer_active = create_offerer(siren="123456789", is_active=True)
    offerer_not_active = create_offerer(siren="123456781", is_active=False)

    PcObject.check_and_save(offerer_active, offerer_not_active)

    # When
    query_only_active = find_filtered_offerers(is_active=True)

    # Then
    assert offerer_active in query_only_active
    assert offerer_not_active not in query_only_active


@pytest.mark.standalone
@clean_database
def test_find_filtered_offerers_with_has_bank_information_param_return_filtered_offerers(app):
    # Given
    offerer_without_bank_information = create_offerer(siren="123456781")
    offerer_with_bank_information = create_offerer()

    bank_information = create_bank_information(bic="AGRIFRPP", iban='DE89370400440532013000',
                                               id_at_providers=offerer_with_bank_information.siren,
                                               offerer=offerer_with_bank_information)

    PcObject.check_and_save(offerer_with_bank_information, offerer_without_bank_information, bank_information)

    # When
    query_with_bank_information = find_filtered_offerers(has_bank_information=True)

    # Then
    assert offerer_with_bank_information in query_with_bank_information
    assert offerer_without_bank_information not in query_with_bank_information


@pytest.mark.standalone
@clean_database
def test_find_filtered_offerers_with_True_has_validated_user_param_return_filtered_offerers(app):
    # Given
    offerer_with_not_validated_user = create_offerer(siren="123456781")
    offerer_with_validated_user = create_offerer(siren="123456782")
    offerer_with_both = create_offerer(siren="123456783")

    validated_user_1 = create_user(email="1@kikou.com", validation_token=None)
    validated_user_2 = create_user(email="2@kikou.com", validation_token=None)
    not_validated_user_1 = create_user(email="3@kikou.com", validation_token="a_token")
    not_validated_user_2 = create_user(email="4@kikou.com", validation_token="another_token")

    user_offerer_validated_user_1 = create_user_offerer(validated_user_1, offerer_with_validated_user)
    user_offerer_validated_user_2 = create_user_offerer(validated_user_2, offerer_with_both)
    user_offerer_not_validated_user_1 = create_user_offerer(not_validated_user_1, offerer_with_not_validated_user)
    user_offerer_not_validated_user_2 = create_user_offerer(not_validated_user_2, offerer_with_both)

    PcObject.check_and_save(user_offerer_validated_user_1, user_offerer_validated_user_2,
                            user_offerer_not_validated_user_1, user_offerer_not_validated_user_2)

    # When
    query_validated_user = find_filtered_offerers(has_validated_user=True)

    # Then
    assert offerer_with_not_validated_user not in query_validated_user
    assert offerer_with_validated_user in query_validated_user
    assert offerer_with_both in query_validated_user


@pytest.mark.standalone
@clean_database
def test_find_filtered_offerers_with_False_has_validated_user_param_return_filtered_offerers(app):
    # Given
    offerer_with_not_validated_user = create_offerer(siren="123456781")
    offerer_with_validated_user = create_offerer(siren="123456782")
    offerer_with_both = create_offerer(siren="123456783")

    validated_user_1 = create_user(email="1@kikou.com", validation_token=None)
    validated_user_2 = create_user(email="2@kikou.com", validation_token=None)
    not_validated_user_1 = create_user(email="3@kikou.com", validation_token="a_token")
    not_validated_user_2 = create_user(email="4@kikou.com", validation_token="another_token")

    user_offerer_validated_user_1 = create_user_offerer(validated_user_1, offerer_with_validated_user)
    user_offerer_validated_user_2 = create_user_offerer(validated_user_2, offerer_with_both)
    user_offerer_not_validated_user_1 = create_user_offerer(not_validated_user_1, offerer_with_not_validated_user)
    user_offerer_not_validated_user_2 = create_user_offerer(not_validated_user_2, offerer_with_both)

    PcObject.check_and_save(user_offerer_validated_user_1, user_offerer_validated_user_2,
                            user_offerer_not_validated_user_1, user_offerer_not_validated_user_2)

    # When
    query_not_validated = find_filtered_offerers(has_validated_user=False)

    # Then
    assert offerer_with_not_validated_user in query_not_validated
    assert offerer_with_validated_user not in query_not_validated
    assert offerer_with_both not in query_not_validated


@pytest.mark.standalone
@clean_database
def test_find_filtered_offerers_with_True_has_not_virtual_venue_param_return_filtered_offerers(app):
    # Given
    offerer_with_only_virtual_venue = create_offerer(siren="123456789")
    offerer_with_both_virtual_and_not_virtual_venue = create_offerer(siren="123456781")

    virtual_venue_1 = create_venue(offerer_with_only_virtual_venue, is_virtual=True, siret=None)
    virtual_venue_2 = create_venue(offerer_with_both_virtual_and_not_virtual_venue, is_virtual=True, siret=None)
    not_virtual_venue = create_venue(offerer_with_both_virtual_and_not_virtual_venue)

    PcObject.check_and_save(virtual_venue_1, virtual_venue_2, not_virtual_venue)

    # When
    query_with_not_virtual = find_filtered_offerers(has_not_virtual_venue=True)

    # Then
    assert offerer_with_only_virtual_venue not in query_with_not_virtual
    assert offerer_with_both_virtual_and_not_virtual_venue in query_with_not_virtual


@pytest.mark.standalone
@clean_database
def test_find_filtered_offerers_with_False_has_not_virtual_venue_param_return_filtered_offerers(app):
    # Given
    offerer_with_only_virtual_venue = create_offerer(siren="123456789")
    offerer_with_both_virtual_and_not_virtual_venue = create_offerer(siren="123456781")

    virtual_venue_1 = create_venue(offerer_with_only_virtual_venue, is_virtual=True, siret=None)
    virtual_venue_2 = create_venue(offerer_with_both_virtual_and_not_virtual_venue, is_virtual=True, siret=None)
    not_virtual_venue = create_venue(offerer_with_both_virtual_and_not_virtual_venue)

    PcObject.check_and_save(virtual_venue_1, virtual_venue_2, not_virtual_venue)

    # When
    query_only_virtual = find_filtered_offerers(has_not_virtual_venue=False)

    # Then
    assert offerer_with_only_virtual_venue in query_only_virtual
    assert offerer_with_both_virtual_and_not_virtual_venue not in query_only_virtual


@pytest.mark.standalone
@clean_database
def test_find_filtered_offerers_with_True_has_validated_venue_param_return_filtered_offerers(app):
    # Given
    offerer_with_not_validated_venue = create_offerer(siren="123456789")
    offerer_with_validated_venue = create_offerer(siren="123456781")
    offerer_with_both = create_offerer(siren="123456782")

    venue_with_not_validated_venue_1 = create_venue(offerer_with_not_validated_venue,
                                                    siret="12345678912341", validation_token="another_token")
    venue_with_validated_venue_1 = create_venue(offerer_with_validated_venue,
                                                siret="12345678912342")
    venue_with_not_validated_venue_2 = create_venue(offerer_with_both,
                                                    siret="12345678912343", validation_token="a_token")
    venue_with_validated_venue_2 = create_venue(offerer_with_both,
                                                siret="12345678912344")

    PcObject.check_and_save(venue_with_not_validated_venue_1, venue_with_validated_venue_1,
                            venue_with_not_validated_venue_2, venue_with_validated_venue_2)

    # When
    query_validated = find_filtered_offerers(has_validated_venue=True)

    # Then
    assert offerer_with_not_validated_venue not in query_validated
    assert offerer_with_validated_venue in query_validated
    assert offerer_with_both in query_validated


@pytest.mark.standalone
@clean_database
def test_find_filtered_offerers_with_False_has_validated_venue_param_return_filtered_offerers(app):
    # Given
    offerer_with_not_validated_venue = create_offerer(siren="123456789")
    offerer_with_validated_venue = create_offerer(siren="123456781")
    offerer_with_both = create_offerer(siren="123456782")

    venue_with_not_validated_venue_1 = create_venue(offerer_with_not_validated_venue,
                                                    siret="12345678912341", validation_token="another_token")
    venue_with_validated_venue_1 = create_venue(offerer_with_validated_venue,
                                                siret="12345678912342")
    venue_with_not_validated_venue_2 = create_venue(offerer_with_both,
                                                    siret="12345678912343", validation_token="a_token")
    venue_with_validated_venue_2 = create_venue(offerer_with_both,
                                                siret="12345678912344")

    PcObject.check_and_save(venue_with_not_validated_venue_1, venue_with_validated_venue_1,
                            venue_with_not_validated_venue_2, venue_with_validated_venue_2)

    # When
    query_not_validated = find_filtered_offerers(has_validated_venue=False)

    # Then
    assert offerer_with_not_validated_venue in query_not_validated
    assert offerer_with_validated_venue not in query_not_validated
    assert offerer_with_both not in query_not_validated


@pytest.mark.standalone
@clean_database
def test_find_filtered_offerers_with_True_has_venue_with_siret_param_return_filtered_offerers(app):
    # Given
    offerer_with_venue_without_siret_comment = create_offerer(siren="123456789")
    offerer_with_venue_without_siret_virtual = create_offerer(siren="123456788")
    offerer_with_venue_with_siret = create_offerer(siren="123456787")
    offerer_with_both_comment = create_offerer(siren="123456786")
    offerer_with_both_virtual = create_offerer(siren="123456785")

    venue_with_no_siret_comment_1 = create_venue(offerer_with_venue_without_siret_comment,
                                                 siret=None, comment="I've no siret")
    venue_with_no_siret_virtual_1 = create_venue(offerer_with_venue_without_siret_virtual,
                                                 siret=None, is_virtual=True)
    venue_with_siret_1 = create_venue(offerer_with_venue_with_siret, siret="12345678912341")
    venue_with_siret_2 = create_venue(offerer_with_both_comment, siret="12345678912342")
    venue_with_siret_3 = create_venue(offerer_with_both_virtual, siret="12345678912343")
    venue_with_no_siret_comment_2 = create_venue(offerer_with_both_comment,
                                                 siret=None, comment="No more siret :/")
    venue_with_no_siret_virtual_2 = create_venue(offerer_with_both_virtual,
                                                 siret=None, is_virtual=True)

    PcObject.check_and_save(venue_with_no_siret_comment_1, venue_with_no_siret_virtual_1, venue_with_siret_1,
                            venue_with_siret_2, venue_with_siret_3, venue_with_no_siret_comment_2,
                            venue_with_no_siret_virtual_2)

    # When
    query_with_siret = find_filtered_offerers(has_venue_with_siret=True)

    # Then
    assert offerer_with_venue_without_siret_comment not in query_with_siret
    assert offerer_with_venue_without_siret_virtual not in query_with_siret
    assert offerer_with_venue_with_siret in query_with_siret
    assert offerer_with_both_comment in query_with_siret
    assert offerer_with_both_virtual in query_with_siret


@pytest.mark.standalone
@clean_database
def test_find_filtered_offerers_with_False_has_venue_with_siret_param_return_filtered_offerers(app):
    # Given
    offerer_with_venue_without_siret_comment = create_offerer(siren="123456789")
    offerer_with_venue_without_siret_virtual = create_offerer(siren="123456788")
    offerer_with_venue_with_siret = create_offerer(siren="123456787")
    offerer_with_both_comment = create_offerer(siren="123456786")
    offerer_with_both_virtual = create_offerer(siren="123456785")

    venue_with_no_siret_comment_1 = create_venue(offerer_with_venue_without_siret_comment,
                                                 siret=None, comment="I've no siret")
    venue_with_no_siret_virtual_1 = create_venue(offerer_with_venue_without_siret_virtual,
                                                 siret=None, is_virtual=True)
    venue_with_siret_1 = create_venue(offerer_with_venue_with_siret, siret="12345678912341")
    venue_with_siret_2 = create_venue(offerer_with_both_comment, siret="12345678912342")
    venue_with_siret_3 = create_venue(offerer_with_both_virtual, siret="12345678912343")
    venue_with_no_siret_comment_2 = create_venue(offerer_with_both_comment,
                                                 siret=None, comment="No more siret :/")
    venue_with_no_siret_virtual_2 = create_venue(offerer_with_both_virtual, siret=None, is_virtual=True)

    PcObject.check_and_save(venue_with_no_siret_comment_1, venue_with_no_siret_virtual_1, venue_with_siret_1,
                            venue_with_siret_2, venue_with_siret_3, venue_with_no_siret_comment_2,
                            venue_with_no_siret_virtual_2)

    # When
    query_whitout_siret = find_filtered_offerers(has_venue_with_siret=False)

    # Then
    assert offerer_with_venue_without_siret_comment in query_whitout_siret
    assert offerer_with_venue_without_siret_virtual in query_whitout_siret
    assert offerer_with_venue_with_siret not in query_whitout_siret
    assert offerer_with_both_comment not in query_whitout_siret
    assert offerer_with_both_virtual not in query_whitout_siret


@pytest.mark.standalone
@clean_database
def test_find_filtered_offerers_with_True_has_validated_user_offerer_param_return_filtered_offerers(app):
    # Given
    offerer_with_not_validated_user_offerer = create_offerer(siren="123456781")
    offerer_with_validated_user_offerer = create_offerer(siren="123456782")
    offerer_with_both = create_offerer(siren="123456783")

    user = create_user()

    user_offerer_validated_1 = create_user_offerer(user, offerer_with_validated_user_offerer)
    user_offerer_validated_2 = create_user_offerer(user, offerer_with_both)
    user_offerer_not_validated_1 = create_user_offerer(user, offerer_with_not_validated_user_offerer,
                                                       validation_token="a_token")
    user_offerer_not_validated_2 = create_user_offerer(user, offerer_with_both, validation_token="another_token")

    PcObject.check_and_save(user_offerer_validated_1, user_offerer_validated_2,
                            user_offerer_not_validated_1, user_offerer_not_validated_2)

    # When
    query_validated = find_filtered_offerers(has_validated_user_offerer=True)

    # Then
    assert offerer_with_not_validated_user_offerer not in query_validated
    assert offerer_with_validated_user_offerer in query_validated
    assert offerer_with_both in query_validated


@pytest.mark.standalone
@clean_database
def test_find_filtered_offerers_with_False_has_validated_user_offerer_param_return_filtered_offerers(app):
    # Given
    offerer_with_not_validated_user_offerer = create_offerer(siren="123456781")
    offerer_with_validated_user_offerer = create_offerer(siren="123456782")
    offerer_with_both = create_offerer(siren="123456783")

    user = create_user()

    user_offerer_validated_1 = create_user_offerer(user, offerer_with_validated_user_offerer)
    user_offerer_validated_2 = create_user_offerer(user, offerer_with_both)
    user_offerer_not_validated_1 = create_user_offerer(user, offerer_with_not_validated_user_offerer,
                                                       validation_token="a_token")
    user_offerer_not_validated_2 = create_user_offerer(user, offerer_with_both, validation_token="another_token")

    PcObject.check_and_save(user_offerer_validated_1, user_offerer_validated_2, user_offerer_not_validated_1,
                            user_offerer_not_validated_2)

    # When
    query_not_validated = find_filtered_offerers(has_validated_user_offerer=False)

    # Then
    assert offerer_with_not_validated_user_offerer in query_not_validated
    assert offerer_with_validated_user_offerer not in query_not_validated
    assert offerer_with_both not in query_not_validated


@pytest.mark.standalone
@clean_database
def test_find_filtered_offerers_with_offer_status_with_VALID_param_return_filtered_offerers(app):
    # Given
    offerer_without_offer = create_offerer(siren="123456781")
    offerer_with_valid_event = create_offerer(siren="123456782")
    offerer_with_expired_event = create_offerer(siren="123456783")
    offerer_with_valid_thing = create_offerer(siren="123456784")
    offerer_with_expired_thing = create_offerer(siren="123456785")
    offerer_with_soft_deleted_thing = create_offerer(siren="123456786")
    offerer_with_soft_deleted_event = create_offerer(siren="123456787")
    offerer_with_not_available_event = create_offerer(siren="123456788")

    venue_without_offer = create_venue(offerer_without_offer)
    venue_with_valid_event = create_venue(offerer_with_valid_event, siret='12345678912346')
    venue_with_expired_event = create_venue(offerer_with_expired_event, siret='12345678912347')
    venue_with_valid_thing = create_venue(offerer_with_valid_thing, siret='12345678912348')
    venue_with_expired_thing = create_venue(offerer_with_expired_thing, siret='12345678912349')
    venue_with_soft_deleted_thing = create_venue(offerer_with_soft_deleted_thing, siret='12345678912342')
    venue_with_soft_deleted_event = create_venue(offerer_with_soft_deleted_event, siret='12345678912343')
    venue_with_not_available_event = create_venue(offerer_with_not_available_event, siret='12345678912344')

    valid_event = create_event_offer(venue_with_valid_event)
    expired_event = create_event_offer(venue_with_expired_event)
    valid_thing = create_thing_offer(venue_with_valid_thing)
    expired_thing = create_thing_offer(venue_with_expired_thing)
    soft_deleted_thing = create_thing_offer(venue_with_soft_deleted_thing)
    soft_deleted_event = create_event_offer(venue_with_soft_deleted_event)
    not_available_event = create_event_offer(venue_with_not_available_event)

    valid_event_occurrence = create_event_occurrence(valid_event,
                                                     beginning_datetime=datetime.utcnow() + timedelta(days=4),
                                                     end_datetime=datetime.utcnow() + timedelta(days=5))
    valid_event_occurrence_soft_deleted = create_event_occurrence(soft_deleted_event,
                                                                  beginning_datetime=datetime.utcnow() + timedelta(
                                                                      days=4),
                                                                  end_datetime=datetime.utcnow() + timedelta(days=5))
    valid_event_occurrence_not_available = create_event_occurrence(not_available_event,
                                                                   beginning_datetime=datetime.utcnow() + timedelta(
                                                                       days=4),
                                                                   end_datetime=datetime.utcnow() + timedelta(days=5))
    expired_event_occurence = create_event_occurrence(expired_event,
                                                      beginning_datetime=datetime(2018, 2, 1),
                                                      end_datetime=datetime(2018, 3, 2))

    valid_stock = create_stock_with_thing_offer(offerer_with_valid_thing, venue_with_valid_thing, valid_thing)
    expired_stock = create_stock_with_thing_offer(offerer_with_expired_thing, venue_with_expired_thing, expired_thing,
                                                  available=0)
    soft_deleted_thing_stock = create_stock_with_thing_offer(offerer_with_soft_deleted_thing,
                                                             venue_with_soft_deleted_thing,
                                                             soft_deleted_thing, soft_deleted=True)

    expired_booking_limit_date_event_stock = create_stock_from_event_occurrence(expired_event_occurence,
                                                                                booking_limit_date=datetime(2018, 1, 1))
    valid_booking_limit_date_event_stock = create_stock_from_event_occurrence(valid_event_occurrence,
                                                                              booking_limit_date=datetime.utcnow() + timedelta(
                                                                                  days=3))
    soft_deleted_event_stock = create_stock_from_event_occurrence(valid_event_occurrence_soft_deleted,
                                                                  soft_deleted=True,
                                                                  booking_limit_date=datetime.utcnow() + timedelta(
                                                                      days=3))
    not_available_event_stock = create_stock_from_event_occurrence(valid_event_occurrence_not_available,
                                                                   available=0,
                                                                   booking_limit_date=datetime.utcnow() + timedelta(
                                                                       days=3))

    PcObject.check_and_save(venue_without_offer, valid_event_occurrence, expired_event_occurence,
                            valid_stock, expired_stock, soft_deleted_thing_stock,
                            expired_booking_limit_date_event_stock,
                            valid_booking_limit_date_event_stock, soft_deleted_event_stock, not_available_event_stock)

    # When
    query_has_valid_offer = find_filtered_offerers(offer_status='VALID')

    # Then
    assert offerer_without_offer not in query_has_valid_offer
    assert offerer_with_valid_event in query_has_valid_offer
    assert offerer_with_expired_event not in query_has_valid_offer
    assert offerer_with_valid_thing in query_has_valid_offer
    assert offerer_with_expired_thing not in query_has_valid_offer
    assert offerer_with_soft_deleted_thing not in query_has_valid_offer
    assert offerer_with_soft_deleted_event not in query_has_valid_offer
    assert offerer_with_not_available_event not in query_has_valid_offer


@pytest.mark.standalone
@clean_database
def test_find_filtered_offerers_with_offer_status_with_EXPIRED_param_return_filtered_offerers(app):
    # Given
    offerer_without_offer = create_offerer(siren="123456781")
    offerer_with_valid_event = create_offerer(siren="123456782")
    offerer_with_expired_event = create_offerer(siren="123456783")
    offerer_with_valid_thing = create_offerer(siren="123456784")
    offerer_with_expired_thing = create_offerer(siren="123456785")
    offerer_with_soft_deleted_thing = create_offerer(siren="123456786")
    offerer_with_soft_deleted_event = create_offerer(siren="123456787")
    offerer_with_not_available_event = create_offerer(siren="123456788")

    venue_without_offer = create_venue(offerer_without_offer)
    venue_with_valid_event = create_venue(offerer_with_valid_event, siret='12345678912346')
    venue_with_expired_event = create_venue(offerer_with_expired_event, siret='12345678912347')
    venue_with_valid_thing = create_venue(offerer_with_valid_thing, siret='12345678912348')
    venue_with_expired_thing = create_venue(offerer_with_expired_thing, siret='12345678912349')
    venue_with_soft_deleted_thing = create_venue(offerer_with_soft_deleted_thing, siret='12345678912342')
    venue_with_soft_deleted_event = create_venue(offerer_with_soft_deleted_event, siret='12345678912343')
    venue_with_not_available_event = create_venue(offerer_with_not_available_event, siret='12345678912344')

    valid_event = create_event_offer(venue_with_valid_event)
    expired_event = create_event_offer(venue_with_expired_event)
    valid_thing = create_thing_offer(venue_with_valid_thing)
    expired_thing = create_thing_offer(venue_with_expired_thing)
    soft_deleted_thing = create_thing_offer(venue_with_soft_deleted_thing)
    soft_deleted_event = create_event_offer(venue_with_soft_deleted_event)
    not_available_event = create_event_offer(venue_with_not_available_event)

    valid_event_occurrence = create_event_occurrence(valid_event,
                                                     beginning_datetime=datetime.utcnow() + timedelta(days=4),
                                                     end_datetime=datetime.utcnow() + timedelta(days=5))
    valid_event_occurrence_soft_deleted = create_event_occurrence(soft_deleted_event,
                                                                  beginning_datetime=datetime.utcnow() + timedelta(
                                                                      days=4),
                                                                  end_datetime=datetime.utcnow() + timedelta(days=5))
    valid_event_occurrence_not_available = create_event_occurrence(not_available_event,
                                                                   beginning_datetime=datetime.utcnow() + timedelta(
                                                                       days=4),
                                                                   end_datetime=datetime.utcnow() + timedelta(days=5))
    expired_event_occurence = create_event_occurrence(expired_event,
                                                      beginning_datetime=datetime(2018, 2, 1),
                                                      end_datetime=datetime(2018, 3, 2))

    valid_stock = create_stock_with_thing_offer(offerer_with_valid_thing, venue_with_valid_thing, valid_thing)
    expired_stock = create_stock_with_thing_offer(offerer_with_expired_thing, venue_with_expired_thing, expired_thing,
                                                  available=0)
    soft_deleted_thing_stock = create_stock_with_thing_offer(offerer_with_soft_deleted_thing,
                                                             venue_with_soft_deleted_thing,
                                                             soft_deleted_thing, soft_deleted=True)

    expired_booking_limit_date_event_stock = create_stock_from_event_occurrence(expired_event_occurence,
                                                                                booking_limit_date=datetime(2018, 1, 1))
    valid_booking_limit_date_event_stock = create_stock_from_event_occurrence(valid_event_occurrence,
                                                                              booking_limit_date=datetime.utcnow() + timedelta(
                                                                                  days=3))
    soft_deleted_event_stock = create_stock_from_event_occurrence(valid_event_occurrence_soft_deleted,
                                                                  soft_deleted=True,
                                                                  booking_limit_date=datetime.utcnow() + timedelta(
                                                                      days=3))
    not_available_event_stock = create_stock_from_event_occurrence(valid_event_occurrence_not_available,
                                                                   available=0,
                                                                   booking_limit_date=datetime.utcnow() + timedelta(
                                                                       days=3))

    PcObject.check_and_save(venue_without_offer, valid_event_occurrence, expired_event_occurence,
                            valid_stock, expired_stock, soft_deleted_thing_stock,
                            expired_booking_limit_date_event_stock,
                            valid_booking_limit_date_event_stock, soft_deleted_event_stock, not_available_event_stock)

    # When
    query_has_expired_offer = find_filtered_offerers(offer_status='EXPIRED')

    # Then
    assert offerer_with_valid_event not in query_has_expired_offer
    assert offerer_without_offer not in query_has_expired_offer
    assert offerer_with_expired_event in query_has_expired_offer
    assert offerer_with_valid_thing not in query_has_expired_offer
    assert offerer_with_expired_thing in query_has_expired_offer
    assert offerer_with_soft_deleted_thing in query_has_expired_offer
    assert offerer_with_soft_deleted_event in query_has_expired_offer
    assert offerer_with_not_available_event in query_has_expired_offer


@pytest.mark.standalone
@clean_database
def test_find_filtered_offerers_with_offer_status_with_WITHOUT_param_return_filtered_offerers(app):
    # Given
    offerer_without_offer = create_offerer(siren="123456781")
    offerer_with_valid_event = create_offerer(siren="123456782")
    offerer_with_expired_event = create_offerer(siren="123456783")
    offerer_with_valid_thing = create_offerer(siren="123456784")
    offerer_with_expired_thing = create_offerer(siren="123456785")
    offerer_with_soft_deleted_thing = create_offerer(siren="123456786")
    offerer_with_soft_deleted_event = create_offerer(siren="123456787")
    offerer_with_not_available_event = create_offerer(siren="123456788")

    venue_without_offer = create_venue(offerer_without_offer)
    venue_with_valid_event = create_venue(offerer_with_valid_event, siret='12345678912346')
    venue_with_expired_event = create_venue(offerer_with_expired_event, siret='12345678912347')
    venue_with_valid_thing = create_venue(offerer_with_valid_thing, siret='12345678912348')
    venue_with_expired_thing = create_venue(offerer_with_expired_thing, siret='12345678912349')
    venue_with_soft_deleted_thing = create_venue(offerer_with_soft_deleted_thing, siret='12345678912342')
    venue_with_soft_deleted_event = create_venue(offerer_with_soft_deleted_event, siret='12345678912343')
    venue_with_not_available_event = create_venue(offerer_with_not_available_event, siret='12345678912344')

    valid_event = create_event_offer(venue_with_valid_event)
    expired_event = create_event_offer(venue_with_expired_event)
    valid_thing = create_thing_offer(venue_with_valid_thing)
    expired_thing = create_thing_offer(venue_with_expired_thing)
    soft_deleted_thing = create_thing_offer(venue_with_soft_deleted_thing)
    soft_deleted_event = create_event_offer(venue_with_soft_deleted_event)
    not_available_event = create_event_offer(venue_with_not_available_event)

    valid_event_occurrence = create_event_occurrence(valid_event,
                                                     beginning_datetime=datetime.utcnow() + timedelta(days=4),
                                                     end_datetime=datetime.utcnow() + timedelta(days=5))
    valid_event_occurrence_soft_deleted = create_event_occurrence(soft_deleted_event,
                                                                  beginning_datetime=datetime.utcnow() + timedelta(
                                                                      days=4),
                                                                  end_datetime=datetime.utcnow() + timedelta(days=5))
    valid_event_occurrence_not_available = create_event_occurrence(not_available_event,
                                                                   beginning_datetime=datetime.utcnow() + timedelta(
                                                                       days=4),
                                                                   end_datetime=datetime.utcnow() + timedelta(days=5))
    expired_event_occurence = create_event_occurrence(expired_event,
                                                      beginning_datetime=datetime(2018, 2, 1),
                                                      end_datetime=datetime(2018, 3, 2))

    valid_stock = create_stock_with_thing_offer(offerer_with_valid_thing, venue_with_valid_thing, valid_thing)
    expired_stock = create_stock_with_thing_offer(offerer_with_expired_thing, venue_with_expired_thing, expired_thing,
                                                  available=0)
    soft_deleted_thing_stock = create_stock_with_thing_offer(offerer_with_soft_deleted_thing,
                                                             venue_with_soft_deleted_thing,
                                                             soft_deleted_thing, soft_deleted=True)

    expired_booking_limit_date_event_stock = create_stock_from_event_occurrence(expired_event_occurence,
                                                                                booking_limit_date=datetime(2018, 1, 1))
    valid_booking_limit_date_event_stock = create_stock_from_event_occurrence(valid_event_occurrence,
                                                                              booking_limit_date=datetime.utcnow() + timedelta(
                                                                                  days=3))
    soft_deleted_event_stock = create_stock_from_event_occurrence(valid_event_occurrence_soft_deleted,
                                                                  soft_deleted=True,
                                                                  booking_limit_date=datetime.utcnow() + timedelta(
                                                                      days=3))
    not_available_event_stock = create_stock_from_event_occurrence(valid_event_occurrence_not_available,
                                                                   available=0,
                                                                   booking_limit_date=datetime.utcnow() + timedelta(
                                                                       days=3))

    PcObject.check_and_save(venue_without_offer, valid_event_occurrence, expired_event_occurence,
                            valid_stock, expired_stock, soft_deleted_thing_stock,
                            expired_booking_limit_date_event_stock,
                            valid_booking_limit_date_event_stock, soft_deleted_event_stock, not_available_event_stock)

    # When
    query_without_offer = find_filtered_offerers(offer_status='WITHOUT')

    # Then
    assert offerer_with_valid_event not in query_without_offer
    assert offerer_without_offer in query_without_offer
    assert offerer_with_expired_event not in query_without_offer
    assert offerer_with_valid_thing not in query_without_offer
    assert offerer_with_expired_thing not in query_without_offer
    assert offerer_with_soft_deleted_thing not in query_without_offer
    assert offerer_with_soft_deleted_event not in query_without_offer
    assert offerer_with_not_available_event not in query_without_offer


@pytest.mark.standalone
@clean_database
def test_find_filtered_offerers_with_offer_status_with_ALL_param_return_filtered_offerers(app):
    # Given
    offerer_without_offer = create_offerer(siren="123456781")
    offerer_with_valid_event = create_offerer(siren="123456782")
    offerer_with_expired_event = create_offerer(siren="123456783")
    offerer_with_valid_thing = create_offerer(siren="123456784")
    offerer_with_expired_thing = create_offerer(siren="123456785")
    offerer_with_soft_deleted_thing = create_offerer(siren="123456786")
    offerer_with_soft_deleted_event = create_offerer(siren="123456787")
    offerer_with_not_available_event = create_offerer(siren="123456788")

    venue_without_offer = create_venue(offerer_without_offer)
    venue_with_valid_event = create_venue(offerer_with_valid_event, siret='12345678912346')
    venue_with_expired_event = create_venue(offerer_with_expired_event, siret='12345678912347')
    venue_with_valid_thing = create_venue(offerer_with_valid_thing, siret='12345678912348')
    venue_with_expired_thing = create_venue(offerer_with_expired_thing, siret='12345678912349')
    venue_with_soft_deleted_thing = create_venue(offerer_with_soft_deleted_thing, siret='12345678912342')
    venue_with_soft_deleted_event = create_venue(offerer_with_soft_deleted_event, siret='12345678912343')
    venue_with_not_available_event = create_venue(offerer_with_not_available_event, siret='12345678912344')

    valid_event = create_event_offer(venue_with_valid_event)
    expired_event = create_event_offer(venue_with_expired_event)
    valid_thing = create_thing_offer(venue_with_valid_thing)
    expired_thing = create_thing_offer(venue_with_expired_thing)
    soft_deleted_thing = create_thing_offer(venue_with_soft_deleted_thing)
    soft_deleted_event = create_event_offer(venue_with_soft_deleted_event)
    not_available_event = create_event_offer(venue_with_not_available_event)

    valid_event_occurrence = create_event_occurrence(valid_event,
                                                     beginning_datetime=datetime.utcnow() + timedelta(days=4),
                                                     end_datetime=datetime.utcnow() + timedelta(days=5))
    valid_event_occurrence_soft_deleted = create_event_occurrence(soft_deleted_event,
                                                                  beginning_datetime=datetime.utcnow() + timedelta(
                                                                      days=4),
                                                                  end_datetime=datetime.utcnow() + timedelta(days=5))
    valid_event_occurrence_not_available = create_event_occurrence(not_available_event,
                                                                   beginning_datetime=datetime.utcnow() + timedelta(
                                                                       days=4),
                                                                   end_datetime=datetime.utcnow() + timedelta(days=5))
    expired_event_occurence = create_event_occurrence(expired_event,
                                                      beginning_datetime=datetime(2018, 2, 1),
                                                      end_datetime=datetime(2018, 3, 2))

    valid_stock = create_stock_with_thing_offer(offerer_with_valid_thing, venue_with_valid_thing, valid_thing)
    expired_stock = create_stock_with_thing_offer(offerer_with_expired_thing, venue_with_expired_thing, expired_thing,
                                                  available=0)
    soft_deleted_thing_stock = create_stock_with_thing_offer(offerer_with_soft_deleted_thing,
                                                             venue_with_soft_deleted_thing,
                                                             soft_deleted_thing, soft_deleted=True)

    expired_booking_limit_date_event_stock = create_stock_from_event_occurrence(expired_event_occurence,
                                                                                booking_limit_date=datetime(2018, 1, 1))
    valid_booking_limit_date_event_stock = create_stock_from_event_occurrence(valid_event_occurrence,
                                                                              booking_limit_date=datetime.utcnow() + timedelta(
                                                                                  days=3))
    soft_deleted_event_stock = create_stock_from_event_occurrence(valid_event_occurrence_soft_deleted,
                                                                  soft_deleted=True,
                                                                  booking_limit_date=datetime.utcnow() + timedelta(
                                                                      days=3))
    not_available_event_stock = create_stock_from_event_occurrence(valid_event_occurrence_not_available,
                                                                   available=0,
                                                                   booking_limit_date=datetime.utcnow() + timedelta(
                                                                       days=3))

    PcObject.check_and_save(venue_without_offer, valid_event_occurrence, expired_event_occurence,
                            valid_stock, expired_stock, soft_deleted_thing_stock,
                            expired_booking_limit_date_event_stock,
                            valid_booking_limit_date_event_stock, soft_deleted_event_stock, not_available_event_stock)

    # When
    query_with_all_offer = find_filtered_offerers(offer_status='ALL')

    # Then
    assert offerer_with_valid_event in query_with_all_offer
    assert offerer_without_offer not in query_with_all_offer
    assert offerer_with_expired_event in query_with_all_offer
    assert offerer_with_valid_thing in query_with_all_offer
    assert offerer_with_expired_thing in query_with_all_offer
    assert offerer_with_soft_deleted_thing in query_with_all_offer
    assert offerer_with_soft_deleted_event in query_with_all_offer
    assert offerer_with_not_available_event in query_with_all_offer


@pytest.mark.standalone
@clean_database
def test_find_filtered_offerers_with_offer_status_with_ALL_param_and_False_has_not_virtual_venues_return_filtered_offerers(
        app):
    # Given
    offerer_with_only_virtual_venue_with_offer = create_offerer(siren="123456785")
    offerer_with_only_virtual_venue_without_offer = create_offerer(siren="123456786")
    offerer_with_both_venues_none_offer = create_offerer(siren="123456781")
    offerer_with_both_venues_offer_on_both = create_offerer(siren="123456782")
    offerer_with_both_venues_offer_on_virtual = create_offerer(siren="123456783")
    offerer_with_both_venues_offer_on_not_virtual = create_offerer(siren="123456784")

    virtual_venue_with_offer_1 = create_venue(offerer_with_only_virtual_venue_with_offer, is_virtual=True, siret=None)
    virtual_venue_without_offer_1 = create_venue(offerer_with_only_virtual_venue_without_offer, is_virtual=True,
                                                 siret=None)
    virtual_venue_without_offer_2 = create_venue(offerer_with_both_venues_none_offer, is_virtual=True, siret=None)
    venue_without_offer_2 = create_venue(offerer_with_both_venues_none_offer, siret="12345678112345")
    virtual_venue_with_offer_3 = create_venue(offerer_with_both_venues_offer_on_both, is_virtual=True, siret=None)
    venue_with_offer_3 = create_venue(offerer_with_both_venues_offer_on_both, siret="12345678212345")
    virtual_venue_with_offer_4 = create_venue(offerer_with_both_venues_offer_on_virtual, is_virtual=True, siret=None)
    venue_without_offer_4 = create_venue(offerer_with_both_venues_offer_on_virtual, siret="12345678312345")
    virtual_venue_without_offer_5 = create_venue(offerer_with_both_venues_offer_on_not_virtual, is_virtual=True,
                                                 siret=None)
    venue_with_offer_5 = create_venue(offerer_with_both_venues_offer_on_not_virtual, siret="12345678412345")

    offer_1 = create_event_offer(virtual_venue_with_offer_1)
    offer_2 = create_event_offer(virtual_venue_with_offer_3)
    offer_3 = create_event_offer(venue_with_offer_3)
    offer_4 = create_event_offer(virtual_venue_with_offer_4)
    offer_5 = create_event_offer(venue_with_offer_5)

    PcObject.check_and_save(offer_1, offer_2, offer_3, offer_4, offer_5, virtual_venue_without_offer_1,
                            virtual_venue_without_offer_2,
                            venue_without_offer_2, venue_without_offer_4, virtual_venue_without_offer_5)

    # When
    query_with_all_offer = find_filtered_offerers(offer_status='ALL', has_not_virtual_venue=False)

    # Then
    assert offerer_with_only_virtual_venue_with_offer in query_with_all_offer
    assert offerer_with_only_virtual_venue_without_offer not in query_with_all_offer
    assert offerer_with_both_venues_none_offer not in query_with_all_offer
    assert offerer_with_both_venues_offer_on_both not in query_with_all_offer
    assert offerer_with_both_venues_offer_on_virtual not in query_with_all_offer
    assert offerer_with_both_venues_offer_on_not_virtual not in query_with_all_offer


@pytest.mark.standalone
@clean_database
def test_find_filtered_offerers_with_offer_status_with_ALL_param_and_True_has_not_virtual_venues_return_filtered_offerers(
        app):
    # Given
    offerer_with_only_virtual_venue_with_offer = create_offerer(siren="123456785")
    offerer_with_only_virtual_venue_without_offer = create_offerer(siren="123456786")
    offerer_with_both_venues_none_offer = create_offerer(siren="123456781")
    offerer_with_both_venues_offer_on_both = create_offerer(siren="123456782")
    offerer_with_both_venues_offer_on_virtual = create_offerer(siren="123456783")
    offerer_with_both_venues_offer_on_not_virtual = create_offerer(siren="123456784")

    virtual_venue_with_offer_1 = create_venue(offerer_with_only_virtual_venue_with_offer, is_virtual=True, siret=None)
    virtual_venue_without_offer_1 = create_venue(offerer_with_only_virtual_venue_without_offer, is_virtual=True,
                                                 siret=None)
    virtual_venue_without_offer_2 = create_venue(offerer_with_both_venues_none_offer, is_virtual=True, siret=None)
    venue_without_offer_2 = create_venue(offerer_with_both_venues_none_offer, siret="12345678112345")
    virtual_venue_with_offer_3 = create_venue(offerer_with_both_venues_offer_on_both, is_virtual=True, siret=None)
    venue_with_offer_3 = create_venue(offerer_with_both_venues_offer_on_both, siret="12345678212345")
    virtual_venue_with_offer_4 = create_venue(offerer_with_both_venues_offer_on_virtual, is_virtual=True, siret=None)
    venue_without_offer_4 = create_venue(offerer_with_both_venues_offer_on_virtual, siret="12345678312345")
    virtual_venue_without_offer_5 = create_venue(offerer_with_both_venues_offer_on_not_virtual, is_virtual=True,
                                                 siret=None)
    venue_with_offer_5 = create_venue(offerer_with_both_venues_offer_on_not_virtual, siret="12345678412345")

    offer_1 = create_event_offer(virtual_venue_with_offer_1)
    offer_2 = create_event_offer(virtual_venue_with_offer_3)
    offer_3 = create_event_offer(venue_with_offer_3)
    offer_4 = create_event_offer(virtual_venue_with_offer_4)
    offer_5 = create_event_offer(venue_with_offer_5)

    PcObject.check_and_save(offer_1, offer_2, offer_3, offer_4, offer_5, virtual_venue_without_offer_1,
                            virtual_venue_without_offer_2,
                            venue_without_offer_2, venue_without_offer_4, virtual_venue_without_offer_5)

    # When
    query_with_all_offer = find_filtered_offerers(offer_status='ALL', has_not_virtual_venue=True)

    # Then
    assert offerer_with_only_virtual_venue_with_offer not in query_with_all_offer
    assert offerer_with_only_virtual_venue_without_offer not in query_with_all_offer
    assert offerer_with_both_venues_none_offer not in query_with_all_offer
    assert offerer_with_both_venues_offer_on_both in query_with_all_offer
    assert offerer_with_both_venues_offer_on_virtual in query_with_all_offer
    assert offerer_with_both_venues_offer_on_not_virtual in query_with_all_offer


@pytest.mark.standalone
@clean_database
def test_find_filtered_offerers_with_default_param_return_all_offerers(app):
    # Given
    offerer_67 = create_offerer(siren="123456781", postal_code="67520")
    offerer_34000 = create_offerer(siren="123456782", postal_code="34000")
    offerer_with_siren = create_offerer(siren="123456784")
    offerer_without_siren = create_offerer(siren=None)
    offerer_with_no_venue = create_offerer(siren="123456786")
    offerer_with_only_virtual_venue = create_offerer(siren="123456787")
    offerer_with_both_venues = create_offerer(siren="123456788")
    offerer_not_validated = create_offerer(siren="123456789", validation_token="a_token")
    offerer_with_bank_information = create_offerer(siren="123456771")

    bank_information = create_bank_information(bic="AGRIFRPP", iban='DE89370400440532013000',
                                               id_at_providers=offerer_with_bank_information.siren,
                                               offerer=offerer_with_bank_information)

    PcObject.check_and_save(bank_information)

    offerer_not_active = create_offerer(siren="123456772", is_active=False)

    virtual_venue_1 = create_venue(offerer_with_only_virtual_venue, siret=None, is_virtual=True)
    virtual_venue_2 = create_venue(offerer_with_both_venues, siret=None, is_virtual=True)
    not_virtual_venue = create_venue(offerer_with_both_venues)

    PcObject.check_and_save(offerer_67, offerer_34000, offerer_with_siren, offerer_without_siren, offerer_with_no_venue,
                            offerer_with_only_virtual_venue, offerer_with_both_venues, offerer_not_validated,
                            offerer_with_bank_information,
                            offerer_not_active, virtual_venue_1, virtual_venue_2, not_virtual_venue)

    # When
    default_query = find_filtered_offerers()

    # Then
    assert offerer_67 in default_query
    assert offerer_34000 in default_query
    assert offerer_with_siren in default_query
    assert offerer_without_siren in default_query
    assert offerer_with_no_venue in default_query
    assert offerer_with_only_virtual_venue in default_query
    assert offerer_with_both_venues in default_query
    assert offerer_not_validated in default_query
    assert offerer_with_bank_information in default_query
    assert offerer_not_active in default_query
