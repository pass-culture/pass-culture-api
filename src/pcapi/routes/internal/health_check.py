import logging

from pcapi.flask_app import public_api
from pcapi.utils import requests
from pcapi.utils.health_checker import check_database_connection
from pcapi.utils.health_checker import read_version_from_file


print("creating logger for route")
logger = logging.getLogger(__name__)


@public_api.route("/selftest/log", methods=["GET"])
def selftest_log():
    response = requests.get("https://example.com")
    logger.info("Log without M object")
    return str(response.status_code), 200


@public_api.route("/health/api", methods=["GET"])
def health_api():
    output = read_version_from_file()
    return output, 200


@public_api.route("/health/database", methods=["GET"])
def health_database():
    database_working = check_database_connection()
    return_code = 200 if database_working else 500
    output = read_version_from_file()
    return output, return_code
