import logging

from pcapi.core.fraud import models as fraud_models
from pcapi.core.users import models as users_models
from pcapi.models import BeneficiaryImport
from pcapi.models import BeneficiaryImportSources
from pcapi.models import ImportStatus
from pcapi.models import db
from pcapi.use_cases.create_beneficiary_from_application import CreateBeneficiaryFromApplication


logger = logging.getLogger()


user_list = []


def update_user(user_list):
    beneficiary_repository = CreateBeneficiaryFromApplication()
    for user_id in user_list:
        user = users_models.User.query.get(user_id)
        jouve_fraud_check = fraud_models.BeneficiaryFraudCheck.query.filter(
            fraud_models.BeneficiaryFraudCheck.type == fraud_models.FraudCheckType.JOUVE,
            fraud_models.BeneficiaryFraudCheck.user == user,
        ).one_or_none()
        if (
            user.beneficiaryFraudResult is None
            or not user.beneficiaryFraudResult.status == fraud_models.FraudStatus.SUBSCRIPTION_ON_HOLD
        ):
            logger.warning("User #%d is not on hold", user.id)
            continue
        if not jouve_fraud_check:
            logger.warning("Cannot reprocess user %d", user.id)
            continue
        logger.info("processing user %d", user.id)
        jouve_content = jouve_fraud_check.source_data()
        db.session.delete(jouve_fraud_check)
        db.session.delete(user.beneficiaryFraudResult)
        db.session.commit()
        beneficiary_repository.execute(application_id=jouve_content.id)


def mark_user_fraud(fraud_list):
    for user_id in fraud_list:
        user = users_models.User.query.get(user_id)
        jouve_fraud_check = fraud_models.BeneficiaryFraudCheck.query.filter(
            fraud_models.BeneficiaryFraudCheck.type == fraud_models.FraudCheckType.JOUVE,
            fraud_models.BeneficiaryFraudCheck.user == user,
        ).one_or_none()
        if (
            user.beneficiaryFraudResult is None
            or not user.beneficiaryFraudResult.status == fraud_models.FraudStatus.SUBSCRIPTION_ON_HOLD
        ):
            logger.warning("User #%d is not on hold", user.id)
            continue
        if not jouve_fraud_check:
            logger.warning("Cannot reprocess user %d", user.id)
            continue
        logger.info("processing user %d", user.id)
        jouve_content = jouve_fraud_check.source_data()
        detail = "Fraude massive novembre 2021 revus par Juliette et JB"
        # update user fraud status to KO
        user.beneficiaryFraudResult.status = fraud_models.FraudStatus.KO
        user.beneficiaryFraudResult.reason = detail
        db.session.add(user.beneficiaryFraudResult)
        beneficiary_import = BeneficiaryImport(
            applicationId=jouve_content.id,
            sourceId=None,
            source=BeneficiaryImportSources.jouve.value,
            beneficiary=user,
        )
        beneficiary_import.setStatus(status=ImportStatus.REJECTED, detail=detail)
        db.session.add(beneficiary_import)
        db.session.commit()
