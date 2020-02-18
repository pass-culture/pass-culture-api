import subprocess
from io import StringIO

from repository.user_queries import find_most_recent_beneficiary_creation_date
from scheduled_tasks.clock import app
from scheduled_tasks.decorators import log_cron
from scheduled_tasks.titelive_clock import app
from scripts.beneficiary import remote_import
from utils.config import API_ROOT_PATH
from utils.logger import logger


@log_cron
def pc_retrieve_offerers_bank_information():
    with app.app_context():
        process = subprocess.Popen('PYTHONPATH="." python scripts/pc.py update_providables'
                                   + ' --provider BankInformationProvider',
                                   shell=True,
                                   cwd=API_ROOT_PATH)
        output, error = process.communicate()
        logger.info(StringIO(output))
        logger.info(StringIO(error))


@log_cron
def pc_remote_import_beneficiaries():
    with app.app_context():
        import_from_date = find_most_recent_beneficiary_creation_date()
        remote_import.run(import_from_date)


@log_cron
def pc_synchronize_titelive_things():
    with app.app_context():
        process = subprocess.Popen('PYTHONPATH="." python scripts/pc.py update_providables'
                                   + ' --provider TiteLiveThings',
                                   shell=True,
                                   cwd=API_ROOT_PATH)
        output, error = process.communicate()
        logger.info(StringIO(output))
        logger.info(StringIO(error))


@log_cron
def pc_synchronize_titelive_descriptions():
    with app.app_context():
        process = subprocess.Popen('PYTHONPATH="." python scripts/pc.py update_providables'
                                   + ' --provider TiteLiveThingDescriptions',
                                   shell=True,
                                   cwd=API_ROOT_PATH)
        output, error = process.communicate()
        logger.info(StringIO(output))
        logger.info(StringIO(error))


@log_cron
def pc_synchronize_titelive_thumbs():
    with app.app_context():
        process = subprocess.Popen('PYTHONPATH="." python scripts/pc.py update_providables'
                                   + ' --provider TiteLiveThingThumbs',
                                   shell=True,
                                   cwd=API_ROOT_PATH)
        output, error = process.communicate()
        logger.info(StringIO(output))
        logger.info(StringIO(error))
