import dataclasses
from enum import Enum

from pcapi import settings


@dataclasses.dataclass
class Template:
    id_prod: int
    id_not_prod: int
    tags: list[str] = dataclasses.field(default_factory=list)
    # Tag your emails to find them more easily cf doc https://developers.sendinblue.com/reference/sendtransacemail

    @property
    def id(self) -> int:
        return self.id_prod if settings.IS_PROD else self.id_not_prod


class TransactionalEmail(Enum):
    EMAIL_CONFIRMATION = Template(id_prod=201, id_not_prod=15, tags=["jeunes_confirmation_mail"])
    EMAIL_ADDRESS_CHANGE_REQUEST = Template(id_prod=142, id_not_prod=17, tags=["changement_email_demande"])
    EMAIL_ADDRESS_CHANGE_CONFIRMATION = Template(id_prod=253, id_not_prod=18, tags=["changement_email_confirmation"])
    EMAIL_DUPLICATE_BENEFICIARY_PRE_SUBCRIPTION_REJECTED = Template(
        id_prod=80, id_not_prod=19, tags=["jeunes_compte_refuse_doublon"]
    )
    FRAUD_SUSPICION = Template(id_prod=82, id_not_prod=24, tags=["jeunes_compte_en_cours_d_analyse"])
    GRANT_USER_CREDIT = Template(id_prod=96, id_not_prod=25, tags=["jeunes_pass_credite_18"])
    NEW_PASSWORD_REQUEST = Template(id_prod=141, id_not_prod=26, tags=["jeunes_nouveau_mdp"])


@dataclasses.dataclass
class SendinblueTransactionalEmailData:
    template: Template
    params: dict
