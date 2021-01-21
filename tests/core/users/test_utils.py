from datetime import datetime
from datetime import timedelta

import jwt

from pcapi import settings
from pcapi.core.users.models import TokenType
from pcapi.core.users.utils import ALGORITHM_HS_256
from pcapi.core.users.utils import create_jwt_token
from pcapi.core.users.utils import encode_jwt_payload


class CreateCustomJwtTokenTest:
    def test_create_jwt_token(self):
        payload = {"userId": 1, "field": "value"}
        token_type = TokenType.EMAIL_VALIDATION
        life_time = timedelta(days=1)

        jwt_token, expiration_date = create_jwt_token(payload, token_type, life_time)

        decoded = jwt.decode(jwt_token, settings.JWT_SECRET_KEY, algorithms=ALGORITHM_HS_256)

        assert decoded["userId"] == payload["userId"]
        assert decoded["field"] == payload["field"]
        assert decoded["type"] == token_type.value
        assert decoded["exp"] == int(expiration_date.timestamp())

    def test_create_jwt_token_without_expiration_date(self):
        payload = {"userId": 1}
        token_type = TokenType.ID_CHECK

        jwt_token, expiration_date = create_jwt_token(payload, token_type)

        decoded = jwt.decode(jwt_token, settings.JWT_SECRET_KEY, algorithms=ALGORITHM_HS_256)

        assert decoded["userId"] == payload["userId"]
        assert decoded["type"] == token_type.value
        assert "exp" not in decoded
        assert not expiration_date

    def test_encode_jwt_payload(self):
        payload = dict(data="value")
        expiration_date = datetime.now()

        jwt_token = encode_jwt_payload(payload, expiration_date)

        decoded = jwt.decode(jwt_token, settings.JWT_SECRET_KEY, algorithms=ALGORITHM_HS_256)

        assert decoded == {"data": "value", "exp": int(expiration_date.timestamp())}

    def test_encode_jwt_payload_without_expiration_date(self):
        payload = dict(data="value")

        jwt_token = encode_jwt_payload(payload)

        decoded = jwt.decode(jwt_token, settings.JWT_SECRET_KEY, algorithms=ALGORITHM_HS_256)

        assert decoded["data"] == "value"
        assert "exp" not in decoded
