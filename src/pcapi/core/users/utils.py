from datetime import datetime
from datetime import timedelta
from typing import Optional
from typing import Tuple

import jwt

from pcapi import settings
from pcapi.core.users.models import ALGORITHM_HS_256
from pcapi.core.users.models import TokenType


def create_jwt_token(
    payload: dict, token_type: TokenType, life_time: Optional[timedelta] = None
) -> Tuple[str, Optional[datetime]]:
    payload["type"] = token_type.value
    expiration_date = datetime.now() + life_time if life_time else None

    return encode_jwt_payload(payload, expiration_date), expiration_date


def encode_jwt_payload(token_payload: dict, expiration_date: Optional[datetime] = None) -> str:
    if expiration_date:
        # do not fill exp key if expiration_date is None or jwt.decode would fail
        token_payload["exp"] = int(expiration_date.timestamp())

    return jwt.encode(
        token_payload,
        settings.JWT_SECRET_KEY,  # type: ignore # known as str in build assertion
        algorithm=ALGORITHM_HS_256,
    ).decode("ascii")


def decode_jwt_token(jwt_token: str) -> dict:
    return jwt.decode(jwt_token, settings.JWT_SECRET_KEY, algorithms=ALGORITHM_HS_256)  # type: ignore # known as str in build assertion


def format_email(email: str) -> str:
    return email.strip().lower()
