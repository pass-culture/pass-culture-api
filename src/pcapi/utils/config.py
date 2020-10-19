""" config """
import os
from logging import INFO as LOG_LEVEL_INFO
from pathlib import Path

from dotenv import load_dotenv


API_ROOT_PATH = Path(os.path.dirname(os.path.realpath(__file__))) / '..'
ENV = os.environ.get('ENV', 'development')
IS_DEV = ENV == 'development'
IS_INTEGRATION = ENV == 'integration'
IS_STAGING = ENV == 'staging'
IS_PROD = ENV == 'production'
IS_TESTING = ENV == 'testing'


# Load env variables
env_path = Path(f'./.env.{ENV}')
load_dotenv(dotenv_path=env_path)

if IS_DEV:
    load_dotenv(dotenv_path='.env.local.secret', override=True)


# General settings
LOG_LEVEL = int(os.environ.get('LOG_LEVEL', LOG_LEVEL_INFO))
REDIS_URL = os.environ.get('REDIS_URL', 'redis://localhost:6379')

if IS_DEV:
    API_URL = 'http://localhost'
    API_APPLICATION_NAME = None
    WEBAPP_URL = 'http://localhost:3000'
    PRO_URL = 'http://localhost:3001'
elif IS_PROD:
    API_URL = 'https://backend.passculture.beta.gouv.fr'
    API_APPLICATION_NAME = 'pass-culture-api'
    WEBAPP_URL = 'https://app.passculture.beta.gouv.fr'
    PRO_URL = 'https://pro.passculture.beta.gouv.fr'
elif IS_TESTING:
    API_URL = 'https://backend.passculture-%s.beta.gouv.fr' % ENV
    API_APPLICATION_NAME = 'pass-culture-api-dev'
    WEBAPP_URL = 'https://app.passculture-%s.beta.gouv.fr' % ENV
    PRO_URL = 'https://pro.testing.passculture.app'
else:
    API_URL = 'https://backend.passculture-%s.beta.gouv.fr' % ENV
    API_APPLICATION_NAME = 'pass-culture-api-%s' % ENV
    WEBAPP_URL = 'https://app.passculture-%s.beta.gouv.fr' % ENV
    PRO_URL = 'https://pro.passculture-%s.beta.gouv.fr' % ENV

BLOB_SIZE = 30


# JOUVE
JOUVE_API_DOMAIN = os.environ.get('JOUVE_API_DOMAIN')
JOUVE_PASSWORD = os.environ.get('JOUVE_PASSWORD')
JOUVE_USERNAME = os.environ.get('JOUVE_USERNAME')
JOUVE_VAULT_GUID = os.environ.get('JOUVE_VAULT_GUID')


# OVH STORAGE
OVH_BUCKET_NAME = os.environ.get('OVH_BUCKET_NAME')

OBJECT_STORAGE_URL = os.environ.get('OBJECT_STORAGE_URL')

# TODO: why do we have 4 different settings here ?
OVH_URL_PATH_TESTING = os.environ.get('OVH_URL_PATH_TESTING')
OVH_USER_TESTING = os.environ.get('OVH_USER_TESTING')
OVH_PASSWORD_TESTING = os.environ.get('OVH_PASSWORD_TESTING')
OVH_TENANT_NAME_TESTING = os.environ.get('OVH_TENANT_NAME_TESTING')
OVH_REGION_NAME_TESTING = os.environ.get('OVH_REGION_NAME_TESTING', 'GRA')

OVH_URL_PATH_STAGING = os.environ.get('OVH_URL_PATH_STAGING')
OVH_USER_STAGING = os.environ.get('OVH_USER_STAGING')
OVH_PASSWORD_STAGING = os.environ.get('OVH_PASSWORD_STAGING')
OVH_TENANT_NAME_STAGING = os.environ.get('OVH_TENANT_NAME_STAGING')
OVH_REGION_NAME_STAGING = os.environ.get('OVH_REGION_NAME_STAGING', 'GRA')

OVH_URL_PATH_PROD = os.environ.get('OVH_URL_PATH_PROD')
OVH_USER_PROD = os.environ.get('OVH_USER_PROD')
OVH_PASSWORD_PROD = os.environ.get('OVH_PASSWORD_PROD')
OVH_TENANT_NAME_PROD = os.environ.get('OVH_TENANT_NAME_PROD')
OVH_REGION_NAME_PROD = os.environ.get('OVH_REGION_NAME_PROD', 'GRA')

OVH_USER = os.environ.get('OVH_USER')
OVH_PASSWORD = os.environ.get('OVH_PASSWORD')
OVH_TENANT_NAME = os.environ.get('OVH_TENANT_NAME')
OVH_REGION_NAME = os.environ.get('OVH_REGION_NAME', 'GRA')



# REDIS
REDIS_OFFER_IDS_CHUNK_SIZE = int(os.environ.get('REDIS_OFFER_IDS_CHUNK_SIZE', 1000))
REDIS_OFFER_IDS_IN_ERROR_CHUNK_SIZE = int(os.environ.get('REDIS_OFFER_IDS_IN_ERROR_CHUNK_SIZE', 1000))
REDIS_VENUE_IDS_CHUNK_SIZE = int(os.environ.get('REDIS_VENUE_IDS_CHUNK_SIZE', 1000))
REDIS_VENUE_PROVIDERS_CHUNK_SIZE = int(os.environ.get('REDIS_VENUE_PROVIDERS_LRANGE_END', 1))


# GOOGLE SPREADSHEET
PC_GOOGLE_KEY = os.environ.get('PC_GOOGLE_KEY')
DASHBOARD_GSHEET_NAME = os.environ.get('DASHBOARD_GSHEET_NAME')


# TITELIVE FTP
FTP_TITELIVE_URI = os.environ.get("FTP_TITELIVE_URI")
FTP_TITELIVE_USER = os.environ.get("FTP_TITELIVE_USER")
FTP_TITELIVE_PWD = os.environ.get("FTP_TITELIVE_PWD")


# RECAPTCHA
RECAPTCHA_SECRET = os.environ.get("RECAPTCHA_SECRET")
RECAPTCHA_REQUIRED_SCORE = os.environ.get("RECAPTCHA_REQUIRED_SCORE", 0.5)
