#!/usr/bin/env python
import os

import sentry_sdk
from sentry_sdk.integrations.flask import FlaskIntegration
import redis
from flask_admin import Admin
from flask_login import LoginManager
from mailjet_rest import Client
from werkzeug.middleware.profiler import ProfilerMiddleware

from admin.install import install_admin_views
from documentation import install_documentation
from flask_app import app
from local_providers.install import install_local_providers
from models.db import db
from models.install import install_activity, install_features, install_discovery_view_v3
from repository.feature_queries import feature_request_profiling_enabled
from routes import install_routes
from utils.config import IS_DEV, REDIS_URL, ENV
from utils.health_checker import read_version_from_file
from utils.mailing import get_contact, \
    MAILJET_API_KEY, \
    MAILJET_API_SECRET, \
    subscribe_newsletter

if IS_DEV is False:
    sentry_sdk.init(
        dsn="https://0470142cf8d44893be88ecded2a14e42@logs.passculture.app/5",
        integrations=[FlaskIntegration()],
        release=read_version_from_file(),
        environment=ENV
    )

login_manager = LoginManager()
admin = Admin(name='pc Back Office', url='/pc/back-office', template_mode='bootstrap3')

if feature_request_profiling_enabled():
    profiling_restrictions = [int(os.environ.get('PROFILE_REQUESTS_LINES_LIMIT', 100))]
    app.config['PROFILE'] = True
    app.wsgi_app = ProfilerMiddleware(app.wsgi_app,
                                      restrictions=profiling_restrictions)

with app.app_context():
    if IS_DEV:
        install_activity()
        install_discovery_view_v3()
        install_local_providers()
        install_features()

    import utils.login_manager

    install_routes()
    install_documentation()
    install_admin_views(admin, db.session)

    app.mailjet_client = Client(auth=(MAILJET_API_KEY, MAILJET_API_SECRET), version='v3')
    app.redis_client = redis.from_url(url=REDIS_URL, decode_responses=True)

    app.get_contact = get_contact
    app.subscribe_newsletter = subscribe_newsletter

if __name__ == '__main__':
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port, debug=IS_DEV, use_reloader=True)
