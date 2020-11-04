import os
from typing import Dict

from pcapi.domain.beneficiary_pre_subscription.beneficiary_pre_subscription import BeneficiaryPreSubscription
from pcapi import settings


def make_duplicate_beneficiary_pre_subscription_rejected_data(
    beneficiary_pre_subscription: BeneficiaryPreSubscription,
) -> Dict:
    beneficiary_email = beneficiary_pre_subscription.email

    return {
        "FromEmail": settings.SUPPORT_EMAIL_ADDRESS,
        "Mj-TemplateID": 1530996,
        "Mj-TemplateLanguage": True,
        "To": beneficiary_email,
    }


def make_not_eligible_beneficiary_pre_subscription_rejected_data(
    beneficiary_pre_subscription: BeneficiaryPreSubscription,
) -> Dict:
    beneficiary_email = beneficiary_pre_subscription.email

    return {
        "FromEmail": settings.SUPPORT_EMAIL_ADDRESS,
        "Mj-TemplateID": 1619528,
        "Mj-TemplateLanguage": True,
        "To": beneficiary_email,
    }
