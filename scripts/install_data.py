from local_providers.install import install_local_providers
from flask import current_app as app
from sqlalchemy_api_handler import logger

from models.install import install_models
from utils.tutorials import upsert_tuto_mediations


@app.manager.command
def install_data():
    with app.app_context():
        install_models()
        upsert_tuto_mediations()
        install_local_providers()
    logger.info("Models and LocalProviders installed")
