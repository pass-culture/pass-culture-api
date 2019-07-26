""" utils thumb """
import os
from pathlib import Path

import pytest
from unittest.mock import patch
from werkzeug.datastructures import FileStorage

from connectors.thumb_storage import read_thumb
from models import ApiErrors, EventType


def test_read_thumb_returns_api_error_when_no_extension_in_filename():
    # given
    dir_path = Path(os.path.dirname(os.path.realpath(__file__)))
    thumb_path = dir_path / '..' / '..' / \
                 'sandboxes' / 'thumbs' / 'products' \
                 / str(EventType.CINEMA)

    files = {
        'thumb': FileStorage(open(thumb_path, mode='rb'))
    }

    # when
    with pytest.raises(ApiErrors) as api_errors:
        read_thumb(files=files, form={})

    # then
    assert api_errors.value.errors['thumb'] == [
        "Cette image manque d'une extension (.png, .jpg, .jpeg, .gif) ou son format n'est pas autoris\u00e9"
    ]

def mocked_requests_get(*args):
    class MockResponse:
        def __init__(self):
            self.content = "it works !"
            self.status_code = 200
            self.headers = {'Content-type': 'image/kikou'}

    return MockResponse()

@patch('connectors.thumb_storage.requests.get', side_effect=mocked_requests_get)
def test_read_thumb_returns_request_content_when_url_is_fine(mocked_requests_get):
    # given
    form = {
        'thumbUrl': 'https://my-image-url.jpg'
    }

    # when
    result = read_thumb(files={}, form=form)

    # then
    assert result == "it works !"

@patch('connectors.thumb_storage.requests.get', side_effect=Exception)
def test_read_thumb_returns_api_error_when_request_raise_ssl_error(mocked_requests_get):
    # given
    form = {
        'thumbUrl': 'https://my-image-url.jpg'
    }
    # when
    with pytest.raises(ApiErrors) as api_errors:
        read_thumb(files={}, form=form)

    # then
    assert api_errors.value.errors['thumbUrl'] == [
        "Impossible de télécharger l'image à cette adresse"
    ]
