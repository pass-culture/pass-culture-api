import os
from datetime import datetime
from typing import List

from connectors.api_demarches_simplifiees import get_application_details
from domain.bank_account import format_raw_iban_or_bic
from domain.demarches_simplifiees import get_all_application_ids_for_procedure
from local_providers.providable_info import ProvidableInfo
from models import BankInformation
from local_providers.local_provider import LocalProvider
from repository import offerer_queries
from repository.local_provider_event_queries import find_latest_sync_end_event
from repository import venue_queries
from utils.date import DATE_ISO_FORMAT
from utils.human_ids import dehumanize


class NoOffererFoundException(Exception):
    pass


class NoVenueFoundException(Exception):
    pass


class VenueWithoutSIRETBankInformationProvider(LocalProvider):
    name = "Demarches simplifiees / IBAN for venue without SIRET"
    can_create = True

    def __init__(self):
        super().__init__()
        self.PROCEDURE_ID = os.environ['DEMARCHES_SIMPLIFIEES_VENUE_WITHOUT_SIRET_PROCEDURE_ID']
        self.TOKEN = os.environ['DEMARCHES_SIMPLIFIEES_TOKEN']

        last_sync_event = find_latest_sync_end_event(self.provider)

        if last_sync_event:
            last_sync_date = last_sync_event.date
        else:
            last_sync_date = datetime(1970, 1, 1)

        self.application_ids = iter(
            get_all_application_ids_for_procedure(self.PROCEDURE_ID, self.TOKEN, last_sync_date)
        )

    def __next__(self) -> List[ProvidableInfo]:
        self.application_id = next(self.application_ids)

        application_response = get_application_details(self.application_id, self.PROCEDURE_ID, self.TOKEN)
        self.application_details = DemarchesSimplifieesMapper.from_venue_without_SIRET_application(application_response)

        offerer = offerer_queries.find_by_id(self.application_details['structureId'])

        if offerer is None:
            raise NoOffererFoundException

        venue = venue_queries.find_by_id(self.application_details['venueId'])

        if venue is None:
            raise NoVenueFoundException

        return self.retrieve_providable_info()

    def retrieve_providable_info(self) -> List[ProvidableInfo]:
        providable_info = ProvidableInfo()
        providable_info.id_at_providers = \
            f"{self.application_details['structureId']}|{self.application_details['venueId']}"

        providable_info.type = BankInformation
        providable_info.date_modified_at_provider = self.application_details['updated_at']
        return [providable_info]

    def fill_object_attributes(self, bank_information: BankInformation):
        bank_information.iban = format_raw_iban_or_bic(self.application_details['IBAN'])
        bank_information.bic = format_raw_iban_or_bic(self.application_details['BIC'])
        bank_information.applicationId = self.application_details['applicationId']
        bank_information.venueId = self.application_details.get('venueId', None)


class DemarchesSimplifieesMapper:
    def _find_value_in_fields(fields, value_name):
        for field in fields:
            if field["type_de_champ"]["libelle"] == value_name:
                return field["value"]

    @classmethod
    def from_venue_without_SIRET_application(cls, response: dict) -> dict:
        application_details = dict()
        application_details['BIC'] = cls._find_value_in_fields(response['dossier']["champs"], "BIC")
        application_details['IBAN'] = cls._find_value_in_fields(response['dossier']["champs"], "IBAN")
        application_details['applicationId'] = response['dossier']["id"]
        application_details['updated_at'] = datetime.strptime(response['dossier']["updated_at"], DATE_ISO_FORMAT)

        url = cls._find_value_in_fields(response['dossier']["champs"], "URL")
        human_structure_id = url.split('/')[-3]
        human_venue_id = url.split('/')[-1]

        application_details['structureId'] = dehumanize(human_structure_id)
        application_details['venueId'] = dehumanize(human_venue_id)

        return application_details
