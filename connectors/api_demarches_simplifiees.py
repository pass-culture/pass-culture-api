import requests


class ApiDemarchesSimplifieesException(Exception):
    pass


def get_all_applications_for_procedure(procedure_id: str, token:str) -> dict:
    response = requests.get(
        f"https://www.demarches-simplifiees.fr/api/v1/procedures/{procedure_id}/dossiers?token={token}&resultats_par_page=1000")

    if response.status_code != 200:
        raise ApiDemarchesSimplifieesException(
            f'Error getting API démarches simplifiées DATA for procedure_id: {procedure_id} and token {token}')

    return response.json()


def get_application_details(application_id: str, procedure_id: str, token: str) -> dict:
    response = requests.get(
        f"https://www.demarches-simplifiees.fr/api/v1/procedures/{procedure_id}/dossiers/{application_id}?token={token}")

    if response.status_code != 200:
        raise ApiDemarchesSimplifieesException(
            f'Error getting API démarches simplifiées DATA for procedure_id: {procedure_id}, application_id: {application_id} and token {token}')

    return response.json()
