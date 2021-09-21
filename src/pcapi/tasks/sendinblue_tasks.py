import logging

from pydantic import BaseModel

from pcapi import settings
from pcapi.core.users.external import sendinblue
from pcapi.models import ApiErrors
from pcapi.tasks.decorator import task


logger = logging.getLogger(__name__)

SENDINBLUE_CONTACTS_QUEUE_NAME = settings.GCP_SENDINBLUE_CONTACTS_QUEUE_NAME


class UpdateSendinblueContactRequest(BaseModel):
    email: str
    attributes: dict
    contact_list_ids: list[int]
    emailBlacklisted: bool


# TODO(viconnex): remove this endpoint when the tasks retargetting the api through this endpoint has been leased (27/09/2021)
@task(SENDINBLUE_CONTACTS_QUEUE_NAME, "/sendinblue/update_contact_attributes")
def update_contact_attributes_task(payload: UpdateSendinblueContactRequest) -> None:
    if not sendinblue.make_update_request(
        payload.email, payload.attributes, payload.contact_list_ids, payload.emailBlacklisted
    ):
        raise ApiErrors(status_code=400)
