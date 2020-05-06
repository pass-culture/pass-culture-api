from local_providers.provider_manager import launch_provider_on_data
from workers.decorators import job_context


@job_context
def pc_synchronize_new_bank_informations(application_id: str, provider_name: str):
    if provider_name == 'offerer':
        launch_provider_on_data("OffererBankInformationProvider", [application_id])
    elif provider_name == 'venue':
        launch_provider_on_data("VenueBankInformationProvider", [application_id])
