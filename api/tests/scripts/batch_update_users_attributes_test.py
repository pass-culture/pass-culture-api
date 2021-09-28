from decimal import Decimal
from unittest.mock import patch

import pytest

from pcapi.core.bookings.factories import IndividualBookingFactory
from pcapi.core.users.external.batch import BATCH_DATETIME_FORMAT
from pcapi.core.users.factories import BeneficiaryGrant18Factory
from pcapi.core.users.factories import UserFactory
import pcapi.notifications.push.testing as push_testing
from pcapi.scripts.batch_update_users_attributes import format_batch_users
from pcapi.scripts.batch_update_users_attributes import format_sendinblue_users
from pcapi.scripts.batch_update_users_attributes import run


@pytest.mark.usefixtures("db_session")
@patch("pcapi.core.users.external.sendinblue.sib_api_v3_sdk.api.contacts_api.ContactsApi.import_contacts")
def test_run(mock_import_contacts):
    """
    Test that two chunks of users are used and therefore two requests are sent.
    """
    UserFactory.create_batch(5)
    run(4)

    assert len(push_testing.requests) == 2
    assert len(mock_import_contacts.call_args_list) == 2


@pytest.mark.usefixtures("db_session")
def test_run_batch_only():
    """
    Test that two chunks of users are used and therefore two requests are sent.
    """
    UserFactory.create_batch(5)
    run(4, synchronize_sendinblue=False)

    assert len(push_testing.requests) == 2


@pytest.mark.usefixtures("db_session")
@patch("pcapi.core.users.external.sendinblue.sib_api_v3_sdk.api.contacts_api.ContactsApi.import_contacts")
def test_run_sendinblue_only(mock_import_contacts):
    """
    Test that two chunks of users are used and therefore two requests are sent.
    """
    UserFactory.create_batch(5)
    run(4, synchronize_batch=False)

    assert len(mock_import_contacts.call_args_list) == 2


@pytest.mark.usefixtures("db_session")
def test_format_batch_user():
    user = BeneficiaryGrant18Factory(deposit__version=1)
    booking = IndividualBookingFactory(individualBooking__user=user)

    res = format_batch_users([user])

    assert len(res) == 1
    assert res[0].attributes == {
        "date(u.date_created)": user.dateCreated.strftime(BATCH_DATETIME_FORMAT),
        "date(u.date_of_birth)": user.dateOfBirth.strftime(BATCH_DATETIME_FORMAT),
        "date(u.deposit_expiration_date)": user.deposit_expiration_date.strftime(BATCH_DATETIME_FORMAT),
        "date(u.last_booking_date)": booking.dateCreated.strftime(BATCH_DATETIME_FORMAT),
        "u.credit": 49000,
        "u.departement_code": "75",
        "u.is_beneficiary": True,
        "u.marketing_push_subscription": True,
        "u.postal_code": None,
        "ut.booking_categories": ["FILM"],
    }


@pytest.mark.usefixtures("db_session")
def test_format_sendinblue_user():
    user = BeneficiaryGrant18Factory(deposit__version=1)
    booking = IndividualBookingFactory(individualBooking__user=user)

    res = format_sendinblue_users([user])

    assert len(res) == 1
    assert res[0].email == user.email
    assert res[0].attributes == {
        "BOOKED_OFFER_CATEGORIES": "FILM",
        "BOOKED_OFFER_SUBCATEGORIES": "SUPPORT_PHYSIQUE_FILM",
        "BOOKING_COUNT": 1,
        "CREDIT": Decimal("490.00"),
        "DATE_CREATED": user.dateCreated,
        "DATE_OF_BIRTH": user.dateOfBirth,
        "DEPARTMENT_CODE": "75",
        "DEPOSIT_ACTIVATION_DATE": user.deposit_activation_date,
        "DEPOSIT_EXPIRATION_DATE": user.deposit_expiration_date,
        "ELIGIBILITY": user.eligibility,
        "FIRSTNAME": "Jeanne",
        "HAS_COMPLETED_ID_CHECK": None,
        "INITIAL_CREDIT": Decimal("500"),
        "IS_BENEFICIARY": True,
        "IS_ELIGIBLE": user.is_eligible,
        "IS_EMAIL_VALIDATED": user.isEmailValidated,
        "IS_PRO": False,
        "LASTNAME": "Doux",
        "LAST_BOOKING_DATE": booking.dateCreated,
        "LAST_FAVORITE_CREATION_DATE": None,
        "LAST_VISIT_DATE": None,
        "MARKETING_EMAIL_SUBSCRIPTION": True,
        "POSTAL_CODE": None,
        "PRODUCT_BRUT_X_USE_DATE": None,
        "USER_ID": user.id,
    }
