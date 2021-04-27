from flask import Blueprint

from pcapi.routes.native import utils
from pcapi.serialization.spec_tree import ExtendedSpecTree
from pcapi.serialization.utils import before_handler


native_v1 = Blueprint("native_v1", __name__)
native_v1.before_request(utils.check_client_version)


JWT_AUTH = "JWTAuth"

security_schemes = {
    JWT_AUTH: {
        "type": "http",
        "scheme": "bearer",
        "bearerFormat": "JWT",
    }
}

api = ExtendedSpecTree("flask", MODE="strict", before=before_handler, PATH="/", security_schemes=security_schemes)
api.register(native_v1)
