from local_providers.provider_manager import synchronize_data_for_provider
from models.feature import FeatureToggle
from repository.user_queries import find_most_recent_beneficiary_creation_date
from scheduled_tasks.decorators import log_cron, cron_context, cron_require_feature
from scripts.beneficiary import remote_import

BANK_INFORMATION_PROVIDER_NAME = "BankInformationProvider"
TITELIVE_THINGS_PROVIDER_NAME = "TiteLiveThings"
TITELIVE_THING_DESCRIPTION_PROVIDER_NAME = "TiteLiveThingDescriptions"
TITELIVE_THING_THUMBS_PROVIDER_NAME = "TiteLiveThingThumbs"


@log_cron
@cron_context
@cron_require_feature(FeatureToggle.SYNCHRONIZE_BANK_INFORMATION)
def retrieve_offerers_bank_information(app):
    synchronize_data_for_provider(BANK_INFORMATION_PROVIDER_NAME)


@log_cron
@cron_context
@cron_require_feature(FeatureToggle.BENEFICIARIES_IMPORT)
def remote_import_beneficiaries(app):
    import_from_date = find_most_recent_beneficiary_creation_date()
    remote_import.run(import_from_date)


@log_cron
@cron_context
@cron_require_feature(FeatureToggle.SYNCHRONIZE_TITELIVE_PRODUCTS)
def synchronize_titelive_things(app):
    synchronize_data_for_provider(TITELIVE_THINGS_PROVIDER_NAME)


@log_cron
@cron_context
@cron_require_feature(FeatureToggle.SYNCHRONIZE_TITELIVE_PRODUCTS_DESCRIPTION)
def synchronize_titelive_descriptions(app):
    synchronize_data_for_provider(TITELIVE_THING_DESCRIPTION_PROVIDER_NAME)


@log_cron
@cron_context
@cron_require_feature(FeatureToggle.SYNCHRONIZE_TITELIVE_PRODUCTS_THUMBS)
def synchronize_titelive_thumbs(app):
    synchronize_data_for_provider(TITELIVE_THING_THUMBS_PROVIDER_NAME)
