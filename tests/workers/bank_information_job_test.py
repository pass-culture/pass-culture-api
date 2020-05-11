from unittest import TestCase
from unittest.mock import patch, call
from datetime import datetime

import pytest
from workers.bank_information_job import synchronize_bank_informations, save_offerer_bank_informations, \
    NoRefererException
from models import ApiErrors

from connectors.api_demarches_simplifiees import DmsApplicationStates
from models.bank_information import BankInformationStatus
from tests.model_creators.generic_creators import create_bank_information, create_offerer
from repository import repository
from tests.conftest import clean_database
from models import BankInformation


def demarche_simplifiee_application_detail_response(siren, bic, iban,
                                                    idx=1,
                                                    updated_at="2019-01-21T18:55:03.387Z",
                                                    state="closed"):
    return {
        "dossier":
        {
            "id": idx,
            "updated_at": updated_at,
            "state": state,
            "entreprise":
            {
                "siren": siren,
            },
            "champs":
            [
                {
                    "value": bic,
                    "type_de_champ":
                    {
                        "id": 352727,
                        "libelle": "BIC",
                        "type_champ": "text",
                        "order_place": 8,
                        "description": ""
                    }
                },
                {
                    "value": iban,
                    "type_de_champ":
                    {
                        "id": 352722,
                        "libelle": "IBAN",
                        "type_champ": "text",
                        "order_place": 9,
                        "description": ""
                    }
                },
            ]
        }
    }


@patch('workers.bank_information_job.save_offerer_bank_informations')
def when_provider_name_is_offerer_should_save_offerer_bank_informations(mock_save_offerer_bank_informations):
    # Given
    application_id = 'id'
    provider_name = 'offerer'

    # When
    synchronize_bank_informations(application_id, provider_name)

    # Then
    assert mock_save_offerer_bank_informations.call_args_list == [
        call('id')
    ]


@patch('workers.bank_information_job.save_venue_bank_informations')
def when_provider_name_is_venue_should_save_venue_bank_informations(mock_save_venue_bank_informations):
    # Given
    application_id = 'id'
    provider_name = 'venue'

    # When
    synchronize_bank_informations(application_id, provider_name)

    # Then
    assert mock_save_venue_bank_informations.call_args_list == [
        call('id')
    ]


@patch('workers.bank_information_job.save_venue_bank_informations')
@patch('workers.bank_information_job.save_offerer_bank_informations')
def when_provider_name_is_another_should_launch_nothing(mock_save_offerer_bank_informations, mock_save_venue_bank_informations):
    # Given
    application_id = ''
    provider_name = ''

    # When
    synchronize_bank_informations(application_id, provider_name)

    # Then
    mock_save_offerer_bank_informations.assert_not_called()
    mock_save_venue_bank_informations.assert_not_called()


class SaveOffererBankInformationsTest:
    class CreateNewBankInformationTest:
        @clean_database
        @patch('workers.bank_information_job.get_application_details')
        def when_dms_state_is_refused_should_create_the_correct_bank_information(self, mock_application_details, app):
            # Given
            application_id = '8'
            offerer = create_offerer(siren='793875030')
            repository.save(offerer)
            mock_application_details.return_value = demarche_simplifiee_application_detail_response(
                siren="793875030", bic="SOGEFRPP", iban="FR7630007000111234567890144", idx=8, state='refused')

            # When
            save_offerer_bank_informations(application_id)

            # Then
            bank_information_count = BankInformation.query.count()
            assert bank_information_count == 1
            bank_information = BankInformation.query.one()
            assert bank_information.bic is None
            assert bank_information.iban is None
            assert bank_information.status == BankInformationStatus.REJECTED

        @clean_database
        @patch('workers.bank_information_job.get_application_details')
        def when_dms_state_is_without_continuation_should_create_the_correct_bank_information(self, mock_application_details, app):
            # Given
            application_id = '8'
            offerer = create_offerer(siren='793875030')
            repository.save(offerer)
            mock_application_details.return_value = demarche_simplifiee_application_detail_response(
                siren="793875030", bic="SOGEFRPP", iban="FR7630007000111234567890144", idx=8, state='without_continuation')

            # When
            save_offerer_bank_informations(application_id)

            # Then
            bank_information_count = BankInformation.query.count()
            assert bank_information_count == 1
            bank_information = BankInformation.query.one()
            assert bank_information.bic is None
            assert bank_information.iban is None
            assert bank_information.status == BankInformationStatus.REJECTED

        @clean_database
        @patch('workers.bank_information_job.get_application_details')
        def when_dms_state_is_closed_should_create_the_correct_bank_information(self, mock_application_details, app):
            # Given
            application_id = '8'
            offerer = create_offerer(siren='793875030')
            repository.save(offerer)
            mock_application_details.return_value = demarche_simplifiee_application_detail_response(
                siren="793875030", bic="SOGEFRPP", iban="FR7630007000111234567890144", idx=8, state='closed')

            # When
            save_offerer_bank_informations(application_id)

            # Then
            bank_information_count = BankInformation.query.count()
            assert bank_information_count == 1
            bank_information = BankInformation.query.one()
            assert bank_information.bic == "SOGEFRPP"
            assert bank_information.iban == "FR7630007000111234567890144"
            assert bank_information.status == BankInformationStatus.ACCEPTED

        @clean_database
        @patch('workers.bank_information_job.get_application_details')
        def when_dms_state_is_received_should_create_the_correct_bank_information(self, mock_application_details,
                                                                                  app):
            # Given
            application_id = '8'
            offerer = create_offerer(siren='793875030')
            repository.save(offerer)
            mock_application_details.return_value = demarche_simplifiee_application_detail_response(
                siren="793875030", bic="SOGEFRPP", iban="FR7630007000111234567890144", idx=8, state='received')

            # When
            save_offerer_bank_informations(application_id)

            # Then
            bank_information_count = BankInformation.query.count()
            assert bank_information_count == 1
            bank_information = BankInformation.query.one()
            assert bank_information.bic is None
            assert bank_information.iban is None
            assert bank_information.status == BankInformationStatus.DRAFT

        @clean_database
        @patch('workers.bank_information_job.get_application_details')
        def when_dms_state_is_initiated_should_create_the_correct_bank_information(self, mock_application_details,
                                                                                   app):
            # Given
            application_id = '8'
            offerer = create_offerer(siren='793875030')
            repository.save(offerer)
            mock_application_details.return_value = demarche_simplifiee_application_detail_response(
                siren="793875030", bic="SOGEFRPP", iban="FR7630007000111234567890144", idx=8, state='initiated')

            # When
            save_offerer_bank_informations(application_id)

            # Then
            bank_information_count = BankInformation.query.count()
            assert bank_information_count == 1
            bank_information = BankInformation.query.one()
            assert bank_information.bic is None
            assert bank_information.iban is None
            assert bank_information.status == BankInformationStatus.DRAFT

        @clean_database
        @patch('workers.bank_information_job.get_application_details')
        def when_no_offerer_siren_specified_should_not_create_bank_information(self, mock_application_details, app):
            # Given
            application_id = '8'
            mock_application_details.return_value = demarche_simplifiee_application_detail_response(
                siren="793875030", bic="SOGEFRPP", iban="FR7630007000111234567890144", idx=8)

            # When
            with pytest.raises(NoRefererException) as error:
                save_offerer_bank_informations(application_id)

            # Then
            bank_information_count = BankInformation.query.count()
            assert bank_information_count == 0
            assert error.value.args == (f'Offerer not found for application id {application_id}.',)

    class UpdateBankInformationByApplicationIdTest:
        @clean_database
        @patch('workers.bank_information_job.get_application_details')
        def when_rib_and_offerer_change_everything_should_be_updated(self, mock_application_details, app):
            # Given
            application_id = '8'
            offerer = create_offerer(siren='793875030')
            new_offerer = create_offerer(siren='793875019')
            bank_information = create_bank_information(
                application_id=8,
                bic='QSDFGH8Z555',
                iban="NL36INGB2682297498",
                offerer=offerer,
            )
            repository.save(offerer, new_offerer, bank_information)
            mock_application_details.return_value = demarche_simplifiee_application_detail_response(
                siren="793875019", bic="SOGEFRPP", iban="FR7630007000111234567890144", idx=8)

            # When
            save_offerer_bank_informations(application_id)

            # Then
            bank_information_count = BankInformation.query.count()
            assert bank_information_count == 1
            bank_information = BankInformation.query.one()
            assert bank_information.bic == 'SOGEFRPP'
            assert bank_information.iban == 'FR7630007000111234567890144'
            assert bank_information.offererId == new_offerer.id

        @clean_database
        @patch('workers.bank_information_job.get_application_details')
        def when_status_change_rib_should_be_correctly_updated(self, mock_application_details, app):
            # Given
            application_id = '8'
            offerer = create_offerer(siren='793875030')
            bank_information = create_bank_information(
                application_id=8,
                bic='QSDFGH8Z555',
                iban="NL36INGB2682297498",
                offerer=offerer,
                status=BankInformationStatus.ACCEPTED
            )
            repository.save(offerer, bank_information)
            mock_application_details.return_value = demarche_simplifiee_application_detail_response(
                siren="793875030", bic="QSDFGH8Z555", iban="NL36INGB2682297498", idx=8, state="initiated")

            # When
            save_offerer_bank_informations(application_id)

            # Then
            bank_information_count = BankInformation.query.count()
            assert bank_information_count == 1
            bank_information = BankInformation.query.one()
            assert bank_information.bic == None
            assert bank_information.iban == None
            assert bank_information.status == BankInformationStatus.DRAFT

        @clean_database
        @patch('workers.bank_information_job.get_application_details')
        def when_overriding_another_bank_information_should_raise(self, mock_application_details, app):
            # Given
            application_id = '8'
            offerer = create_offerer(siren='793875030')
            other_offerer = create_offerer(siren='793875019')
            bank_information = create_bank_information(
                application_id=8,
                bic='QSDFGH8Z555',
                iban="NL36INGB2682297498",
                offerer=offerer,
            )
            other_bank_information = create_bank_information(
                application_id=79,
                bic='QSDFGH8Z555',
                iban="NL36INGB2682297498",
                offerer=other_offerer,
            )
            repository.save(offerer, other_offerer, bank_information, other_bank_information)
            mock_application_details.return_value = demarche_simplifiee_application_detail_response(
                siren="793875019", bic="QSDFGH8Z555", iban="NL36INGB2682297498", idx=8)

            # When
            with pytest.raises(ApiErrors) as errors:
                save_offerer_bank_informations(application_id)

            # Then
            bank_information_count = BankInformation.query.count()
            assert bank_information_count == 2
            print(errors.value.errors)
            assert errors.value.errors['"offererId"'] == [
                'Une entrée avec cet identifiant existe déjà dans notre base de données']

    class OverrideBankInformationByReffererTest:
        @clean_database
        @patch('workers.bank_information_job.get_application_details')
        def when_receive_new_closed_application_should_override_previous_one(self, mock_application_details, app):
            # Given
            application_id = '8'
            offerer = create_offerer(siren='793875030')
            bank_information = create_bank_information(
                application_id=79,
                bic='QSDFGH8Z555',
                iban="NL36INGB2682297498",
                offerer=offerer,
                date_modified_at_last_provider=datetime(2018, 1, 1)
            )
            repository.save(offerer, bank_information)
            mock_application_details.return_value = demarche_simplifiee_application_detail_response(
                siren="793875030", bic="SOGEFRPP", iban="FR7630007000111234567890144", idx=8)

            # When
            save_offerer_bank_informations(application_id)

            # Then
            bank_information_count = BankInformation.query.count()
            assert bank_information_count == 1
            bank_information = BankInformation.query.one()
            assert bank_information.bic == 'SOGEFRPP'
            assert bank_information.iban == 'FR7630007000111234567890144'
            assert bank_information.applicationId == 8

        @clean_database
        @patch('workers.bank_information_job.get_application_details')
        def when_receive_new_application_with_draft_state_should_update_previously_rejected_bank_information(self, mock_application_details, app):
            # Given
            application_id = '8'
            offerer = create_offerer(siren='793875030')
            bank_information = create_bank_information(
                application_id=79,
                bic=None,
                iban=None,
                offerer=offerer,
                date_modified_at_last_provider=datetime(2018, 1, 1),
                status=BankInformationStatus.REJECTED
            )
            repository.save(offerer, bank_information)
            mock_application_details.return_value = demarche_simplifiee_application_detail_response(
                siren="793875030", bic="SOGEFRPP", iban="FR7630007000111234567890144", idx=8, state="initiated")

            # When
            save_offerer_bank_informations(application_id)

            # Then
            bank_information_count = BankInformation.query.count()
            assert bank_information_count == 1
            bank_information = BankInformation.query.one()
            assert bank_information.bic == None
            assert bank_information.iban == None
            assert bank_information.status == BankInformationStatus.DRAFT

        @clean_database
        @patch('workers.bank_information_job.get_application_details')
        def when_receive_new_application_with_lower_status_should_reject(self, mock_application_details, app):
            # Given
            application_id = '8'
            offerer = create_offerer(siren='793875030')
            bank_information = create_bank_information(
                application_id=79,
                bic='QSDFGH8Z555',
                iban="NL36INGB2682297498",
                offerer=offerer,
                date_modified_at_last_provider=datetime(2018, 1, 1),
                status=BankInformationStatus.ACCEPTED
            )
            repository.save(offerer, bank_information)
            mock_application_details.return_value = demarche_simplifiee_application_detail_response(
                siren="793875030", bic="SOGEFRPP", iban="FR7630007000111234567890144", idx=8, state="initiated")

            # When
            save_offerer_bank_informations(application_id)

            # Then
            bank_information_count = BankInformation.query.count()
            assert bank_information_count == 1
            bank_information = BankInformation.query.one()
            assert bank_information.bic == 'QSDFGH8Z555'
            assert bank_information.iban == "NL36INGB2682297498"
            assert bank_information.status == BankInformationStatus.ACCEPTED
            assert bank_information.applicationId == 79

        @clean_database
        @patch('workers.bank_information_job.get_application_details')
        def when_receive_older_application_should_reject(self, mock_application_details, app):
            # Given
            application_id = '8'
            offerer = create_offerer(siren='793875030')
            bank_information = create_bank_information(
                application_id=79,
                bic='QSDFGH8Z555',
                iban="NL36INGB2682297498",
                offerer=offerer,
                date_modified_at_last_provider=datetime(2020, 1, 1)
            )
            repository.save(offerer, bank_information)
            mock_application_details.return_value = demarche_simplifiee_application_detail_response(
                siren="793875030", bic="SOGEFRPP", iban="FR7630007000111234567890144", idx=8)

            # When
            save_offerer_bank_informations(application_id)

            # Then
            bank_information_count = BankInformation.query.count()
            assert bank_information_count == 1
            bank_information = BankInformation.query.one()
            assert bank_information.bic == 'QSDFGH8Z555'
            assert bank_information.iban == "NL36INGB2682297498"
            assert bank_information.status == BankInformationStatus.ACCEPTED
            assert bank_information.applicationId == 79
