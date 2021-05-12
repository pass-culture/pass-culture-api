from typing import Optional

from pcapi.core.users.models import User
from pcapi.domain.beneficiary_pre_subscription.beneficiary_pre_subscription import BeneficiaryPreSubscription
from pcapi.infrastructure.repository.beneficiary import beneficiary_pre_subscription_sql_converter
from pcapi.repository import repository


class BeneficiarySQLRepository:
    @classmethod
    def save(cls, beneficiary_pre_subscription: BeneficiaryPreSubscription, user: Optional[User] = None) -> User:
        user_sql_entity = beneficiary_pre_subscription_sql_converter.to_model(beneficiary_pre_subscription, user=user)
        repository.save(user_sql_entity)
        return user_sql_entity

    @classmethod
    def reject(
        cls, beneficiary_pre_subscription: BeneficiaryPreSubscription, detail: str, user: Optional[User]
    ) -> None:
        beneficiary_import = beneficiary_pre_subscription_sql_converter.to_rejected_model(
            beneficiary_pre_subscription, detail=detail, user=user
        )
        repository.save(beneficiary_import)
