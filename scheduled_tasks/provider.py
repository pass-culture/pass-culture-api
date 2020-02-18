from local_providers.provider_manager import synchronize_data_for_provider
from repository.user_queries import find_most_recent_beneficiary_creation_date
from scheduled_tasks.clock import app
from scheduled_tasks.decorators import log_cron
from scheduled_tasks.titelive_clock import app
from scripts.beneficiary import remote_import

BANK_INFORMATION_PROVIDER_NAME = "BankInformationProvider"
TITELIVE_THINGS_PROVIDER_NAME = "TiteLiveThings"
TITELIVE_THING_DESCRIPTION_PROVIDER_NAME = "TiteLiveThingDescriptions"
TITELIVE_THING_THUMBS_PROVIDER_NAME = "TiteLiveThingThumbs"


@log_cron
def pc_retrieve_offerers_bank_information():
    with app.app_context():
        synchronize_data_for_provider(BANK_INFORMATION_PROVIDER_NAME)


@log_cron
def pc_remote_import_beneficiaries():
    with app.app_context():
        import_from_date = find_most_recent_beneficiary_creation_date()
        remote_import.run(import_from_date)


@log_cron
def pc_synchronize_titelive_things():
    with app.app_context():
        synchronize_data_for_provider(TITELIVE_THINGS_PROVIDER_NAME)


@log_cron
def pc_synchronize_titelive_descriptions():
    with app.app_context():
        synchronize_data_for_provider(TITELIVE_THING_DESCRIPTION_PROVIDER_NAME)


@log_cron
def pc_synchronize_titelive_thumbs():
    with app.app_context():
        synchronize_data_for_provider(TITELIVE_THING_THUMBS_PROVIDER_NAME)
