""" config """
from logging import INFO as LOG_LEVEL_INFO
import os
from pathlib import Path

from dotenv import load_dotenv


API_ROOT_PATH = Path(os.path.dirname(os.path.realpath(__file__))) / '..'
ENV = os.environ.get('ENV', 'development')
IS_DEV = ENV == 'development'
IS_INTEGRATION = ENV == 'integration'
IS_STAGING = ENV == 'staging'
IS_PROD = ENV == 'production'
IS_TESTING = ENV == 'testing'


# Load configuration files
env_path = Path(f'./.env.{ENV}')
load_dotenv(dotenv_path=env_path)

if IS_DEV:
    load_dotenv(dotenv_path='.env.local.secret', override=True)
if os.environ.get("RUN_ENV") == "tests":
    load_dotenv(dotenv_path='.env.testauto', override=True)

LOG_LEVEL = int(os.environ.get('LOG_LEVEL', LOG_LEVEL_INFO))


# TODO: Why isn't it in the .env.{ENV} ?
if IS_DEV:
    API_URL = 'http://localhost'
    API_APPLICATION_NAME = None
    WEBAPP_URL = 'http://localhost:3000'
    PRO_URL = 'http://localhost:3001'
    NATIVE_APP_URL = 'passculture://app.passculture.testing'
elif IS_PROD:
    API_URL = 'https://backend.passculture.beta.gouv.fr'
    API_APPLICATION_NAME = 'pass-culture-api'
    WEBAPP_URL = 'https://app.passculture.beta.gouv.fr'
    PRO_URL = 'https://pro.passculture.beta.gouv.fr'
    NATIVE_APP_URL = 'passculture://app.passculture'
elif IS_TESTING:
    API_URL = f'https://backend.passculture-{ENV}.beta.gouv.fr'
    API_APPLICATION_NAME = 'pass-culture-api-dev'
    WEBAPP_URL = f'https://app.passculture-{ENV}.beta.gouv.fr'
    PRO_URL = 'https://pro.testing.passculture.app'
    NATIVE_APP_URL = f'passculture://app.passculture.{ENV}'
else:
    API_URL = f'https://backend.passculture-{ENV}.beta.gouv.fr'
    API_APPLICATION_NAME = f'pass-culture-api-{ENV}'
    WEBAPP_URL = f'https://app.passculture-{ENV}.beta.gouv.fr'
    PRO_URL = f'https://pro.passculture-{ENV}.beta.gouv.fr'
    NATIVE_APP_URL = f'passculture://app.passculture.{ENV}'

BLOB_SIZE = 30


# TODO: ensure sentry does not log _KEY nor _PWD (?!?) nor TOKEN

# GENERAL
SUPPORT_EMAIL_ADDRESS = os.environ.get('SUPPORT_EMAIL_ADDRESS')
ADMINISTRATION_EMAIL_ADDRESS = os.environ.get('ADMINISTRATION_EMAIL_ADDRESS')
DEV_EMAIL_ADDRESS = os.environ.get('DEV_EMAIL_ADDRESS')


# DB
DATABASE_URL = os.environ.get('DATABASE_URL')
DATABASE_POOL_SIZE = int(os.environ.get('DATABASE_POOL_SIZE', 20))


# REDIS
REDIS_URL = os.environ.get('REDIS_URL', 'redis://localhost:6379')
REDIS_OFFER_IDS_CHUNK_SIZE = int(os.environ.get('REDIS_OFFER_IDS_CHUNK_SIZE', 1000))
REDIS_OFFER_IDS_IN_ERROR_CHUNK_SIZE = int(os.environ.get('REDIS_OFFER_IDS_IN_ERROR_CHUNK_SIZE', 1000))
REDIS_VENUE_IDS_CHUNK_SIZE = int(os.environ.get('REDIS_VENUE_IDS_CHUNK_SIZE', 1000))
REDIS_VENUE_PROVIDERS_CHUNK_SIZE = int(os.environ.get('REDIS_VENUE_PROVIDERS_LRANGE_END', 1))


# ALGOLIA
ALGOLIA_API_KEY = os.environ.get('ALGOLIA_API_KEY')
ALGOLIA_APPLICATION_ID = os.environ.get('ALGOLIA_APPLICATION_ID')
ALGOLIA_INDEX_NAME = os.environ.get('ALGOLIA_INDEX_NAME')

ALGOLIA_SYNC_WORKERS_POOL_SIZE = int(os.environ.get('ALGOLIA_SYNC_WORKERS_POOL_SIZE', 10))
ALGOLIA_WAIT_TIME_FOR_AVAILABLE_WORKER = 60


# JOUVE
JOUVE_API_DOMAIN = os.environ.get('JOUVE_API_DOMAIN')
JOUVE_PASSWORD = os.environ.get('JOUVE_PASSWORD')
JOUVE_USERNAME = os.environ.get('JOUVE_USERNAME')
JOUVE_VAULT_GUID = os.environ.get('JOUVE_VAULT_GUID')


# TITELIVE
FTP_TITELIVE_URI = os.environ.get("FTP_TITELIVE_URI")
FTP_TITELIVE_USER = os.environ.get("FTP_TITELIVE_USER")
FTP_TITELIVE_PWD = os.environ.get("FTP_TITELIVE_PWD")


# RECAPTCHA
RECAPTCHA_API_URL = 'https://www.google.com/recaptcha/api/siteverify'
RECAPTCHA_SECRET = os.environ.get("RECAPTCHA_SECRET")
RECAPTCHA_REQUIRED_SCORE = os.environ.get("RECAPTCHA_REQUIRED_SCORE", 0.5)
RECAPTCHA_ERROR_CODES = {
    'missing-input-secret': 'The secret parameter is missing.',
    'invalid-input-secret': 'The secret parameter is invalid or malformed.',
    'missing-input-response': 'The response parameter is missing.',
    'invalid-input-response': 'The response parameter is invalid or malformed.',
    'bad-request': 'The request is invalid or malformed.',
    'timeout-or-duplicate': 'The response is no longer valid: either is too old or has been used previously.',
}


# GOOGLE SPREADSHEET
GOOGLE_KEY = os.environ.get("PC_GOOGLE_KEY")
GOOGLE_DASHBOARD_SPREADSHEET_NAME = os.environ.get('DASHBOARD_GSHEET_NAME')


# SCALINGO
SCALINGO_APP_TOKEN = os.environ.get('SCALINGO_APP_TOKEN')
SCALINGO_AUTH_URL = 'https://auth.scalingo.com/v1'
SCALINGO_API_URL = 'https://api.osc-fr1.scalingo.com/v1'
SCALINGO_API_REGION = "osc-fr1"
SCALINGO_API_CONTAINER_SIZE = "L"


# DEMARCHES SIMPLIFIEES (DEM_SIMP)
DEMARCHES_SIMPLIFIEES_OFFERER_PROCEDURE_ID = os.environ.get('DEMARCHES_SIMPLIFIEES_RIB_OFFERER_PROCEDURE_ID')
DEMARCHES_SIMPLIFIEES_VENUE_PROCEDURE_ID = os.environ.get('DEMARCHES_SIMPLIFIEES_RIB_VENUE_PROCEDURE_ID')
DEMARCHES_SIMPLIFIEES_TOKEN = os.environ.get('DEMARCHES_SIMPLIFIEES_TOKEN')
DEMARCHES_SIMPLIFIEES_WEBHOOK_TOKEN = os.environ.get('DEMARCHES_SIMPLIFIEES_WEBHOOK_TOKEN')


# TODO: fix this nonsense !
DEMARCHES_SIMPLIFIEES_ENROLLMENT_PROCEDURE_ID = int(
    os.environ.get('DEMARCHES_SIMPLIFIEES_ENROLLMENT_PROCEDURE_ID', 88)
)
DEMARCHES_SIMPLIFIEES_OLD_ENROLLMENT_PROCEDURE_ID = int(os.environ.get(
    'DEMARCHES_SIMPLIFIEES_ENROLLMENT_PROCEDURE_ID', 0
))
DEMARCHES_SIMPLIFIEES_NEW_ENROLLMENT_PROCEDURE_ID = int(os.environ.get(
    'DEMARCHES_SIMPLIFIEES_ENROLLMENT_PROCEDURE_ID_v2', 0
))


# MAILJET
MAILJET_API_KEY = os.environ.get('MAILJET_API_KEY')
MAILJET_API_SECRET = os.environ.get('MAILJET_API_SECRET')
MAILJET_NOT_YET_ELIGIBLE_LIST_ID = os.environ.get('MAILJET_NOT_YET_ELIGIBLE_LIST_ID')


# OBJECT STORAGE
OBJECT_STORAGE_URL = os.environ.get('OBJECT_STORAGE_URL')


# OVH
OVH_USER = os.environ.get('OVH_USER')
OVH_PASSWORD = os.environ.get('OVH_PASSWORD')
OVH_TENANT_NAME = os.environ.get('OVH_TENANT_NAME')
OVH_REGION_NAME = os.environ.get('OVH_REGION_NAME', 'GRA')
OVH_BUCKET_NAME = os.environ.get('OVH_BUCKET_NAME')
# TODO: wait, what is this below ? can we remove it ?
OVH_USER_TESTING = os.environ.get('OVH_USER_TESTING')
OVH_PASSWORD_TESTING = os.environ.get('OVH_PASSWORD_TESTING')
OVH_TENANT_NAME_TESTING = os.environ.get('OVH_TENANT_NAME_TESTING')
OVH_REGION_NAME_TESTING = os.environ.get('OVH_REGION_NAME_TESTING', 'GRA')
OVH_URL_PATH_TESTING = os.environ.get('OVH_URL_PATH_TESTING')
OVH_USER_STAGING = os.environ.get('OVH_USER_STAGING')
OVH_PASSWORD_STAGING = os.environ.get('OVH_PASSWORD_STAGING')
OVH_TENANT_NAME_STAGING = os.environ.get('OVH_TENANT_NAME_STAGING')
OVH_REGION_NAME_STAGING = os.environ.get('OVH_REGION_NAME_STAGING', 'GRA')
OVH_URL_PATH_STAGING = os.environ.get('OVH_URL_PATH_STAGING')
OVH_USER_PROD = os.environ.get('OVH_USER_PROD')
OVH_PASSWORD_PROD = os.environ.get('OVH_PASSWORD_PROD')
OVH_TENANT_NAME_PROD = os.environ.get('OVH_TENANT_NAME_PROD')
OVH_REGION_NAME_PROD = os.environ.get('OVH_REGION_NAME_PROD', 'GRA')
OVH_URL_PATH_PROD = os.environ.get('OVH_URL_PATH_PROD')
