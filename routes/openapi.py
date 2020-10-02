from apispec import APISpec
from apispec.ext.marshmallow import MarshmallowPlugin
from apispec_webframeworks.flask import FlaskPlugin

from flask_app import app


spec = APISpec(
    title="Pass culture API",
    version="1.0.0",
    openapi_version="3.0.3",
    plugins=[FlaskPlugin(), MarshmallowPlugin()],
)


with app.test_request_context():
    # Routes need to be imported within the context manager, otherwise
    # Flask raises a RuntimeError: "Working outside of application
    # context".
    from routes import users

    spec.path(view=users.patch_profile)


if __name__ == '__main__':
    # On peut aussi exporter en JSON:
    # print(json.dumps(spec.to_dict()))
    print(spec.to_yaml())
