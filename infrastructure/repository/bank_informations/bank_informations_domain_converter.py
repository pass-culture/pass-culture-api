from datetime import datetime

from domain.bank_informations.bank_informations import BankInformations
from models import BankInformation as BankInformationsSQLEntity
from infrastructure.repository.stock import stock_domain_converter
from infrastructure.repository.beneficiary import beneficiary_domain_converter
from utils.token import random_token


def to_domain(bank_informations_sql_entity: BankInformationsSQLEntity) -> BankInformations:

    return BankInformations(application_id=bank_informations_sql_entity.applicationId,
                            status=bank_informations_sql_entity.status,
                            iban=bank_informations_sql_entity.iban,
                            bic=bank_informations_sql_entity.bic,
                            date_modified_at_last_provider=bank_informations_sql_entity.dateModifiedAtLastProvider)


def to_model(bank_informations: BankInformations) -> BankInformationsSQLEntity:
    bank_informations_sql_entity = BankInformationsSQLEntity()
    bank_informations_sql_entity.applicationId = bank_informations.application_id
    bank_informations_sql_entity.status = bank_informations.status
    bank_informations_sql_entity.iban = bank_informations.iban
    bank_informations_sql_entity.bic = bank_informations.bic
    bank_informations_sql_entity.offererId = bank_informations.offerer_id
    bank_informations_sql_entity.venueId = bank_informations.venue_id

    return bank_informations_sql_entity
