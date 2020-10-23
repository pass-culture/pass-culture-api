import os
import re
import typing
from datetime import datetime

# Loading variables should always be the first thing, before any other load
from pcapi.load_environment_variables import load_environment_variables
load_environment_variables()

import flask.wrappers
import redis
import sentry_sdk
from flask import Flask, \
    g, \
    request, \
    Blueprint
from flask_admin import Admin
from flask_cors import CORS
from flask_login import LoginManager
from mailjet_rest import Client
from sentry_sdk.integrations.flask import FlaskIntegration
from spectree import SpecTree
from sqlalchemy import orm
from werkzeug.middleware.profiler import ProfilerMiddleware

from pcapi.models.db import db
from pcapi.repository.feature_queries import feature_request_profiling_enabled
from pcapi.serialization.utils import before_handler
from pcapi.utils.config import IS_DEV, \
    ENV
from pcapi.utils.config import REDIS_URL
from pcapi.utils.health_checker import read_version_from_file
from pcapi.utils.json_encoder import EnumJSONEncoder
from pcapi.utils.logger import json_logger
from pcapi.utils.mailing import MAILJET_API_KEY, \
    MAILJET_API_SECRET


if IS_DEV is False:
    sentry_sdk.init(
        dsn="https://0470142cf8d44893be88ecded2a14e42@logs.passculture.app/5",
        integrations=[FlaskIntegration()],
        release=read_version_from_file(),
        environment=ENV
    )

app = Flask(__name__, static_url_path='/static')

api = SpecTree("flask", MODE="strict", before=before_handler)
api.register(app)

login_manager = LoginManager()
admin = Admin(name='pc Back Office', url='/pc/back-office',
              template_mode='bootstrap3')

if feature_request_profiling_enabled():
    profiling_restrictions = [
        int(os.environ.get('PROFILE_REQUESTS_LINES_LIMIT', 100))]
    app.config['PROFILE'] = True
    app.wsgi_app = ProfilerMiddleware(  # type: ignore
        app.wsgi_app,
        restrictions=profiling_restrictions,
    )

app.secret_key = os.environ.get('FLASK_SECRET', '+%+3Q23!zbc+!Dd@')
app.json_encoder = EnumJSONEncoder
app.config['SQLALCHEMY_DATABASE_URI'] = os.environ.get('DATABASE_URL')
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
app.config['SQLALCHEMY_ECHO'] = False
app.config['SESSION_COOKIE_HTTPONLY'] = True
app.config['SESSION_COOKIE_SECURE'] = not IS_DEV
app.config['REMEMBER_COOKIE_HTTPONLY'] = True
app.config['REMEMBER_COOKIE_SECURE'] = not IS_DEV
app.config['REMEMBER_COOKIE_DURATION'] = 90 * 24 * 3600
app.config['PERMANENT_SESSION_LIFETIME'] = 90 * 24 * 3600
app.config['FLASK_ADMIN_SWATCH'] = 'flatly'
app.config['FLASK_ADMIN_FLUID_LAYOUT'] = True


@app.before_request
def before_request() -> None:
    g.start = datetime.utcnow()


@app.after_request
def log_request_details(response: flask.wrappers.Response) -> flask.wrappers.Response:
    request_duration = datetime.utcnow() - g.start
    request_duration_in_milliseconds = round(request_duration.total_seconds() * 1000, 2)
    request_data = {
        "statusCode": response.status_code,
        "method": request.method,
        "route": request.url_rule,
        "path": request.path,
        "queryParams": request.query_string.decode('UTF-8'),
        "duration": request_duration_in_milliseconds,
        "size": response.headers.get('Content-Length', type=int),
        "from": "flask"
    }

    json_logger.info("request details", extra=request_data)
    response.headers["X-Frame-Options"] = "SAMEORIGIN"
    response.headers["X-Content-Type-Options"] = "nosniff"
    response.headers["X-XSS-Protection"] = "1; mode=block"
    response.headers["Strict-Transport-Security"] = "31536000; includeSubDomains; preload"

    return response


@app.teardown_request
def remove_db_session(
        exc: typing.Optional[Exception] = None,  # pylint: disable=unused-argument
) -> None:
    try:
        db.session.remove()
    except AttributeError:
        pass


admin.init_app(app)
db.init_app(app)
orm.configure_mappers()
login_manager.init_app(app)

public_api = Blueprint('Public API', __name__)
CORS(
    public_api,
    resources={
        r"/*": {"origins": "*"}
    },
    supports_credentials=True
)

private_api = Blueprint('Private API', __name__)
CORS(
    private_api,
    resources={
        r"/*": {"origins": re.compile(os.environ.get('CORS_ALLOWED_ORIGIN'))}
    },
    supports_credentials=True
)

app.url_map.strict_slashes = False

with app.app_context():
    app.mailjet_client = Client(
        auth=(MAILJET_API_KEY, MAILJET_API_SECRET), version='v3')
    app.redis_client = redis.from_url(url=REDIS_URL, decode_responses=True)
