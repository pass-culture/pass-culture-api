import os
from datetime import datetime
from typing import Callable, Dict, List, Optional

from models.bank_information import BankInformationStatus
from connectors.api_demarches_simplifiees import get_all_applications_for_procedure, DmsApplicationStates, \
    get_application_details
from domain.bank_account import format_raw_iban_or_bic
from utils.date import DATE_ISO_FORMAT
from utils.logger import logger
from domain.bank_information import check_offerer_presence, check_venue_presence, check_venue_queried_by_name, status_weight, \
    CannotRegisterBankInformation

OFFERER_PROCEDURE_ID = os.environ.get(
    'DEMARCHES_SIMPLIFIEES_RIB_OFFERER_PROCEDURE_ID')
VENUE_PROCEDURE_ID = os.environ.get(
    'DEMARCHES_SIMPLIFIEES_RIB_VENUE_PROCEDURE_ID')
TOKEN = os.environ.get('DEMARCHES_SIMPLIFIEES_TOKEN')
FIELD_FOR_VENUE_WITH_SIRET = "Si vous souhaitez renseigner les coordonn\u00e9es bancaires d'un lieu avec SIRET, merci de saisir son SIRET :"
FIELD_FOR_VENUE_WITHOUT_SIRET = "Si vous souhaitez renseigner les coordonn\u00e9es bancaires d'un lieu sans SIRET, merci de saisir le \"Nom du lieu\", \u00e0 l'identique de celui dans le pass Culture Pro :"


class ApplicationDetail(object):
    def __init__(self, siren: str, status: str, application_id: int, iban: str, bic: str, modification_date: datetime, siret: Optional[str] = None, venue_name: Optional[str] = None):
        self.siren = siren
        self.status = status
        self.application_id = application_id
        self.iban = iban
        self.bic = bic
        self.siret = siret
        self.venue_name = venue_name
        self.modification_date = modification_date


def get_all_application_ids_for_demarche_simplifiee(
        procedure_id: str, token: str, last_update: datetime = None, accepted_states: DmsApplicationStates = DmsApplicationStates
) -> List[int]:
    current_page = 1
    number_of_pages = 1
    applications = []

    while current_page <= number_of_pages:
        api_response = get_all_applications_for_procedure(
            procedure_id, token, page=current_page, results_per_page=100)
        number_of_pages = api_response['pagination']['nombre_de_page']
        logger.info(
            f'[IMPORT DEMARCHES SIMPLIFIEES] page {current_page} of {number_of_pages}')

        applications_to_process = [application for application in api_response['dossiers'] if
                                   _has_requested_state(application, accepted_states) and _was_last_updated_after(application, last_update)]
        logger.info(
            f'[IMPORT DEMARCHES SIMPLIFIEES] {len(applications_to_process)} applications to process')
        applications += applications_to_process

        current_page += 1

    logger.info(
        f'[IMPORT DEMARCHES SIMPLIFIEES] Total : {len(applications)} applications')

    return [application['id'] for application in _sort_applications_by_date(applications)]


def get_closed_application_ids_for_demarche_simplifiee(
        procedure_id: str, token: str, last_update: datetime
) -> List[int]:
    return get_all_application_ids_for_demarche_simplifiee(procedure_id, token, last_update, accepted_states=[DmsApplicationStates.closed])


def get_offerer_bank_information_application_details_by_application_id(application_id: str) -> ApplicationDetail:
    response_application_details = get_application_details(
        application_id, procedure_id=OFFERER_PROCEDURE_ID, token=TOKEN)

    application_details = ApplicationDetail(
        siren=response_application_details['dossier']['entreprise']['siren'],
        status=_get_status_from_demarches_simplifiees_application_state(
            response_application_details['dossier']['state']),
        application_id=int(response_application_details['dossier']["id"]),
        iban=format_raw_iban_or_bic(
            _find_value_in_fields(
                response_application_details['dossier']["champs"], "IBAN")),
        bic=format_raw_iban_or_bic(
            _find_value_in_fields(
                response_application_details['dossier']["champs"], "BIC")),
        modification_date=datetime.strptime(
            response_application_details['dossier']['updated_at'], DATE_ISO_FORMAT)
    )
    return application_details


def get_venue_bank_information_application_details_by_application_id(application_id: str) -> ApplicationDetail:
    response_application_details = get_application_details(
        application_id, procedure_id=VENUE_PROCEDURE_ID, token=TOKEN)

    application_details = ApplicationDetail(
        siren=response_application_details['dossier']['entreprise']['siren'],
        status=_get_status_from_demarches_simplifiees_application_state(
            response_application_details['dossier']['state']),
        application_id=int(response_application_details['dossier']["id"]),
        iban=format_raw_iban_or_bic(
            _find_value_in_fields(
                response_application_details['dossier']["champs"], "IBAN")),
        bic=format_raw_iban_or_bic(
            _find_value_in_fields(
                response_application_details['dossier']["champs"], "BIC")),
        siret=_find_value_in_fields(
            response_application_details['dossier']["champs"], FIELD_FOR_VENUE_WITH_SIRET),
        venue_name=_find_value_in_fields(
            response_application_details['dossier']["champs"], FIELD_FOR_VENUE_WITHOUT_SIRET),
        modification_date=datetime.strptime(
            response_application_details['dossier']['updated_at'], DATE_ISO_FORMAT)
    )
    return application_details


def _has_requested_state(application: dict, states: datetime) -> bool:
    return DmsApplicationStates[application['state']] in states


def _was_last_updated_after(application: dict, last_update: datetime = None) -> bool:
    if(not last_update):
        return True
    return datetime.strptime(application['updated_at'], DATE_ISO_FORMAT) >= last_update


def _sort_applications_by_date(applications: List) -> List:
    return sorted(applications, key=lambda application: datetime.strptime(application['updated_at'], DATE_ISO_FORMAT))


def _get_status_from_demarches_simplifiees_application_state(state: str) -> BankInformationStatus:
    try:
        state = DmsApplicationStates[state]
    except KeyError:
        raise CannotRegisterBankInformation(
            f'Unknown Demarches Simplifiées state {state}')
    rejected_states = [DmsApplicationStates.refused,
                       DmsApplicationStates.without_continuation]
    accepted_states = [DmsApplicationStates.closed]
    draft_states = [DmsApplicationStates.received,
                    DmsApplicationStates.initiated]
    if state in rejected_states:
        return BankInformationStatus.REJECTED
    elif state in accepted_states:
        return BankInformationStatus.ACCEPTED
    elif state in draft_states:
        return BankInformationStatus.DRAFT


def _find_value_in_fields(fields: List[Dict], value_name: str):
    for field in fields:
        if field["type_de_champ"]["libelle"] == value_name:
            return field["value"]
