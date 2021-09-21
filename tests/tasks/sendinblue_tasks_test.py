from unittest.mock import patch

import pytest

from pcapi import settings
from pcapi.core.testing import override_settings
from pcapi.tasks.cloud_task import AUTHORIZATION_HEADER_KEY
from pcapi.tasks.cloud_task import AUTHORIZATION_HEADER_VALUE


pytestmark = pytest.mark.usefixtures("db_session")


@override_settings(SENDINBLUE_API_KEY="lacledusucces")
@patch("pcapi.core.users.external.sendinblue.requests")
def test_legacy_sendinblue_task(request_mock, client):
    response = client.post(
        f"{settings.API_URL}/cloud-tasks/sendinblue/update_contact_attributes",
        json={
            "contact_list_ids": [123],
            "email": "montrerl@example.com",
            "attributes": {"TEXTE_À": True},
            "emailBlacklisted": False,
        },
        headers={AUTHORIZATION_HEADER_KEY: AUTHORIZATION_HEADER_VALUE},
    )
    assert response.status_code == 204

    request_mock.post.assert_called_once_with(
        "https://api.sendinblue.com/v3/contacts",
        headers={
            "Accept": "application/json",
            "Content-Type": "application/json",
            "api-key": "lacledusucces",
        },
        json={
            "attributes": {"TEXTE_À": True},
            "email": "montrerl@example.com",
            "emailBlacklisted": False,
            "listIds": [123],
            "updateEnabled": True,
        },
    )
