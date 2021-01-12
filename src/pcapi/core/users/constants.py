from datetime import timedelta
from enum import Enum


RESET_PASSWORD_TOKEN_LIFE_TIME = timedelta(hours=24)
EMAIL_VALIDATION_TOKEN_LIFE_TIME = timedelta(hours=24)
EMAIL_CHANGE_TOKEN_LIFE_TIME = timedelta(hours=24)
ID_CHECK_TOKEN_LIFE_TIME = timedelta(days=1)

ELIGIBILITY_AGE = 18
ACCOUNT_CREATION_MINIMUM_AGE = 16


class SuspensionReason(Enum):
    def __str__(self) -> str:
        return str(self.value)

    END_OF_CONTRACT = "end of contract"
    END_OF_ELIGIBILITY = "end of eligibility"
    FRAUD = "fraud"
    UPON_USER_REQUEST = "upon user request"


SUSPENSION_REASON_CHOICES = (
    (SuspensionReason.END_OF_ELIGIBILITY, "fin d'éligibilité"),
    (SuspensionReason.END_OF_CONTRACT, "fin de contrat"),
    (SuspensionReason.FRAUD, "fraude"),
    (SuspensionReason.UPON_USER_REQUEST, "demande de l'utilisateur"),
)

assert set(_t[0] for _t in SUSPENSION_REASON_CHOICES) == set(SuspensionReason)
