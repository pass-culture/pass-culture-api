from datetime import datetime
from typing import Callable

from connectors.api_demarches_simplifiees import get_all_applications_for_procedure
from utils.date import DATE_ISO_FORMAT


def get_all_application_ids_for_procedure(
        procedure_id: str, token: str, last_update: datetime,
        get_all_applications: Callable = get_all_applications_for_procedure):
    api_response = get_all_applications(procedure_id, token, results_per_page=1000)
    applications = sorted(api_response['dossiers'], key=lambda k: datetime.strptime(k['updated_at'], DATE_ISO_FORMAT))
    application_ids_to_process = [application['id'] for application in applications if
                                  _needs_processing(application, last_update)]
    return application_ids_to_process


def _needs_processing(application: dict, last_update: datetime) -> dict:
    return _is_closed(application) and _was_last_updated_after(application, last_update)


def _is_closed(application: dict) -> dict:
    return application['state'] == 'closed'


def _was_last_updated_after(application, last_update: datetime):
    return datetime.strptime(application['updated_at'], DATE_ISO_FORMAT) >= last_update
