from local_providers.install import install_local_providers
from models.install import install_models, install_database_extensions
from flask import current_app as app

from utils.tutorials import upsert_tuto_mediations
from utils.logger import logger


@app.manager.command
def install_data():
    with app.app_context():
        install_models()
        upsert_tuto_mediations()
        install_local_providers()
    logger.info("Models and LocalProviders installed")


@app.manager.command
def install_data_for_metabase():
    with app.app_context():
        install_database_extensions()
        install_models()
    logger.info("Models and LocalProviders installed")
