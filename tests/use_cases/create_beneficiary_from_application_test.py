from datetime import datetime
from unittest.mock import patch

from freezegun import freeze_time
from tests.conftest import clean_database

from domain.beneficiary.beneficiary_pre_subscription import \
    BeneficiaryPreSubscription
from models import BeneficiaryImport, UserSQLEntity
from models.beneficiary_import_status import ImportStatus
from models.deposit import Deposit
from use_cases.create_beneficiary_from_application import \
    create_beneficiary_from_application


@patch('use_cases.create_beneficiary_from_application.send_raw_email')
@patch('use_cases.create_beneficiary_from_application.send_activation_email')
@patch('domain.password.random_token')
@patch('infrastructure.repository.beneficiary.beneficiary_pre_subscription_sql_converter.random_password')
@patch('use_cases.create_beneficiary_from_application.BeneficiaryJouveRepository.get_application_by')
@freeze_time('2020-10-15 09:00:00')
@clean_database
def test_saved_a_beneficiary_from_application(stubed_get_application_by,
                                              stubed_random_password,
                                              stubed_random_token,
                                              mocked_send_activation_email,
                                              stubed_send_raw_email,
                                              app):
    # Given
    application_id = 7
    stubed_get_application_by.return_value = BeneficiaryPreSubscription(
        date_of_birth=datetime(1995, 2, 5),
        postal_code='35123',
        email='rennes@example.org',
        first_name='Thomas',
        civility='Mme',
        last_name='DURAND',
        phone_number='0123456789',
        activity='Apprenti',
    )
    stubed_random_password.return_value = b'random-password'
    stubed_random_token.return_value = 'token'

    # When
    create_beneficiary_from_application(application_id)

    # Then
    beneficiary = UserSQLEntity.query.one()
    assert beneficiary.activity == 'Apprenti'
    assert beneficiary.canBookFreeOffers == True
    assert beneficiary.civility == 'Mme'
    assert beneficiary.dateOfBirth == datetime(1995, 2, 5)
    assert beneficiary.departementCode == '35'
    assert beneficiary.email == 'rennes@example.org'
    assert beneficiary.firstName == 'Thomas'
    assert beneficiary.hasSeenTutorials == False
    assert beneficiary.isAdmin == False
    assert beneficiary.lastName == 'DURAND'
    assert beneficiary.password == b'random-password'
    assert beneficiary.phoneNumber == '0123456789'
    assert beneficiary.postalCode == '35123'
    assert beneficiary.publicName == 'Thomas DURAND'
    assert beneficiary.resetPasswordToken == 'token'
    assert beneficiary.resetPasswordTokenValidityLimit == datetime(2020, 11, 14, 9)

    deposit = Deposit.query.one()
    assert deposit.amount == 500
    assert deposit.source == 'dossier jouve [7]'
    assert deposit.userId == beneficiary.id

    beneficiary_import = BeneficiaryImport.query.one()
    assert beneficiary_import.currentStatus == ImportStatus.CREATED
    assert beneficiary_import.applicationId == application_id

    mocked_send_activation_email.assert_called_once_with(user=beneficiary, send_email=stubed_send_raw_email)
