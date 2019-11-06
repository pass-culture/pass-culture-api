from flask import Flask
from flasgger import Swagger

swagger_config = {
    "headers": [],
    "specs": [
        {
            "version": "0.0.2",
            "title": "Api v2",
            "endpoint": 'v2_spec',
            "description": 'This is the version 2 of our API',
            "route": '/v2/bookings/token/',
            "swagger_ui_css": '/static/swagger-ui.css',
        }
    ],
    "static_url_path": "/flasgger_static",
    "specs_route": "/documentation/swagger/",
    "swagger": '2.0',
}

app = Flask(__name__)

app.config["SWAGGER"]= {
    "title": "DOCUMENTATION API",
    "uiversion": 3
    }

swag = Swagger(app, template_file='bookings_token_specifications_v2.json', config=swagger_config)

if __name__ == '__main__':
    app.run(debug=True)
