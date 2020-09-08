from datetime import datetime
from unittest.mock import MagicMock, call, patch

import pytest
from freezegun import freeze_time
from tests.infrastructure.repository.beneficiary import \
    beneficiary_jouve_creators

from domain.beneficiary_pre_subscription.beneficiary_pre_subscription import \
    BeneficiaryPreSubscription
from infrastructure.repository.beneficiary.beneficiary_jouve_repository import ApiJouveException, \
    BeneficiaryJouveRepository


@freeze_time('2020-10-15 09:00:00')
@patch('infrastructure.repository.beneficiary.beneficiary_jouve_repository.JOUVE_API_DOMAIN', 'https://jouve.com')
@patch('infrastructure.repository.beneficiary.beneficiary_jouve_repository.JOUVE_PASSWORD', 'secret-password')
@patch('infrastructure.repository.beneficiary.beneficiary_jouve_repository.JOUVE_USERNAME', 'username')
@patch('infrastructure.repository.beneficiary.beneficiary_jouve_repository.JOUVE_VAULT_GUID', '12')
@patch('infrastructure.repository.beneficiary.beneficiary_jouve_repository.requests.post')
def test_calls_jouve_api_with_previously_fetched_token(mocked_requests_post):
    # Given
    token = 'token-for-tests'
    application_id = 5

    get_token_response = MagicMock(status_code=200)
    get_token_response.json = MagicMock(return_value=beneficiary_jouve_creators.get_token_detail_response(token))

    get_application_by_json = beneficiary_jouve_creators.get_application_by_detail_response(
        address='18 avenue des fleurs',
        application_id=application_id,
        birth_date='08/24/1995',
        city='RENNES',
        email='rennes@example.org',
        first_name='Céline',
        gender='F',
        last_name='DURAND',
        phone_number='0123456789',
        postal_code='35123',
        status='Apprenti'
    )
    get_application_by_response = MagicMock(status_code=200)
    get_application_by_response.json = MagicMock(return_value=get_application_by_json)

    mocked_requests_post.side_effect = [
        get_token_response,
        get_application_by_response
    ]

    # When
    beneficiary_pre_subscription = BeneficiaryJouveRepository().get_application_by(application_id)

    # Then
    assert mocked_requests_post.call_args_list[0] == call(
        'https://jouve.com/REST/server/authenticationtokens',
        headers={'Content-Type': 'application/json'},
        json={
            'Username': 'username',
            'Password': 'secret-password',
            'VaultGuid': '12',
            'Expiration': '2020-10-15T10:00:00'
        })
    assert mocked_requests_post.call_args_list[1] == call(
        'https://jouve.com/REST/vault/extensionmethod/VEM_GetJeuneByID',
        data=str(application_id),
        headers={'X-Authentication': token})
    assert isinstance(beneficiary_pre_subscription, BeneficiaryPreSubscription)
    assert beneficiary_pre_subscription.activity == 'Apprenti'
    assert beneficiary_pre_subscription.address == '18 avenue des fleurs'
    assert beneficiary_pre_subscription.application_id == 5
    assert beneficiary_pre_subscription.city == 'RENNES'
    assert beneficiary_pre_subscription.civility == 'Mme'
    assert beneficiary_pre_subscription.date_of_birth == datetime(1995, 8, 24)
    assert beneficiary_pre_subscription.department_code == '35'
    assert beneficiary_pre_subscription.email == 'rennes@example.org'
    assert beneficiary_pre_subscription.first_name == 'Céline'
    assert beneficiary_pre_subscription.last_name == 'DURAND'
    assert beneficiary_pre_subscription.phone_number == '0123456789'
    assert beneficiary_pre_subscription.postal_code == '35123'
    assert beneficiary_pre_subscription.public_name == 'Céline DURAND'


@patch('infrastructure.repository.beneficiary.beneficiary_jouve_repository.requests.post')
def test_raise_exception_when_password_is_invalid(stubed_requests_post):
    # Given
    application_id = '5'
    stubed_requests_post.return_value = MagicMock(status_code=400)

    # When
    with pytest.raises(ApiJouveException) as api_jouve_exception:
        BeneficiaryJouveRepository().get_application_by(application_id)

    # Then
    assert str(api_jouve_exception.value) == 'Error 400 getting API jouve authentication token'


@patch('infrastructure.repository.beneficiary.beneficiary_jouve_repository.requests.post')
def test_raise_exception_when_token_is_invalid(stubed_requests_post):
    # Given
    token = 'token-for-tests'
    application_id = '5'

    get_token_response = MagicMock(status_code=200)
    get_token_response.json = MagicMock(return_value=beneficiary_jouve_creators.get_token_detail_response(token))

    get_application_by_json = beneficiary_jouve_creators.get_application_by_detail_response()
    get_application_by_response = MagicMock(status_code=400)
    get_application_by_response.json = MagicMock(return_value=get_application_by_json)

    stubed_requests_post.side_effect = [
        get_token_response,
        get_application_by_response
    ]

    # When
    with pytest.raises(ApiJouveException) as api_jouve_exception:
        BeneficiaryJouveRepository().get_application_by(application_id)

    # Then
    assert str(api_jouve_exception.value) == 'Error 400 getting API jouve GetJouveByID with id: 5'
