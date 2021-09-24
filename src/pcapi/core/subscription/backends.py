import logging

from pcapi import settings
from pcapi.connectors.api_demarches_simplifiees import get_application_details
from pcapi.connectors.beneficiaries import jouve_backend
from pcapi.core.fraud.api import on_dms_fraud_check
from pcapi.core.fraud.api import on_jouve_result
from pcapi.core.subscription.models import BeneficiaryPreSubscription
from pcapi.core.users.api import create_reset_password_token
from pcapi.domain import user_emails
from pcapi.domain.beneficiary_pre_subscription.exceptions import BeneficiaryIsADuplicate
from pcapi.domain.beneficiary_pre_subscription.exceptions import CantRegisterBeneficiary
from pcapi.domain.beneficiary_pre_subscription.exceptions import FraudDetected
from pcapi.domain.beneficiary_pre_subscription.exceptions import SuspiciousFraudDetected
from pcapi.domain.beneficiary_pre_subscription.fraud_validator import validate_fraud
from pcapi.domain.beneficiary_pre_subscription.validator import validate
from pcapi.infrastructure.repository.beneficiary.beneficiary_sql_repository import BeneficiarySQLRepository
from pcapi.models import ImportStatus
from pcapi.models.beneficiary_import import BeneficiaryImportSources
from pcapi.repository.beneficiary_import_queries import save_beneficiary_import_with_status
from pcapi.repository.user_queries import find_user_by_email
from pcapi.scripts.beneficiary import remote_import as dms_remote_import


logger = logging.getLogger(__name__)


class ExitProcess(Exception):
    pass


class BaseBeneficiaryBackend:
    def no_preexisting_account_error(self, application_id, beneficiary_pre_subscription):
        save_beneficiary_import_with_status(
            ImportStatus.ERROR,
            application_id,
            source=self.SOURCE,
            source_id=self.SOURCE_ID,
            detail=f"Aucun utilisateur trouvé pour l'email {beneficiary_pre_subscription.email}",
        )
        raise ExitProcess()

    def reject_user(self, application_id, reason, preexisting_account, beneficiary_pre_subscription, is_eligible):
        logger.warning(
            "Couldn't register user from application",
            extra={
                "applicationId": application_id,
                "reason": reason,
            },
        )
        self.beneficiary_repository.reject(beneficiary_pre_subscription, detail=reason, user=preexisting_account)
        user_emails.send_rejection_email_to_beneficiary_pre_subscription(
            beneficiary_pre_subscription=beneficiary_pre_subscription,
            beneficiary_is_eligible=is_eligible,
        )
        raise ExitProcess()

    def execute(
        self,
        application_id: int,
        run_fraud_detection: bool = True,
        ignore_id_piece_number_field: bool = False,
        fraud_detection_ko: bool = False,
    ):
        return self.process_pre_subscription(
            application_id=application_id,
            run_fraud_detection=run_fraud_detection,
            ignore_id_piece_number_field=ignore_id_piece_number_field,
            fraud_detection_ko=fraud_detection_ko,
        )

    def process_pre_subscription(
        self,
        application_id: int,
        run_fraud_detection: bool = True,
        ignore_id_piece_number_field: bool = False,
        fraud_detection_ko: bool = False,
    ) -> None:
        try:
            raw_result = self.get_data_from_remote(application_id)
            beneficiary_pre_subscription = self.parse_remote_data(
                application_id, raw_result, ignore_id_piece_number_field=ignore_id_piece_number_field
            )

            preexisting_account = find_user_by_email(beneficiary_pre_subscription.email)
            if not preexisting_account:
                self.no_preexisting_account_error(application_id, beneficiary_pre_subscription)

            try:
                self.process_result(preexisting_account, raw_result)
            except Exception as exc:
                logger.exception("Error on jouve result: %s", exc)
                raise ExitProcess()

            try:
                validate(
                    beneficiary_pre_subscription,
                    preexisting_account=preexisting_account,
                    ignore_id_piece_number_field=ignore_id_piece_number_field,
                )
                if fraud_detection_ko:
                    raise FraudDetected("Forced by 'fraud_detection_ko' script argument")
                if run_fraud_detection:
                    validate_fraud(beneficiary_pre_subscription)

            except SuspiciousFraudDetected:
                user_emails.send_fraud_suspicion_email(beneficiary_pre_subscription)
                raise ExitProcess()
            except FraudDetected as cant_register_beneficiary_exception:
                # detail column cannot contain more than 255 characters
                detail = f"Fraud controls triggered: {cant_register_beneficiary_exception}"[:255]
                self.beneficiary_repository.reject(
                    beneficiary_pre_subscription,
                    detail=detail,
                    user=preexisting_account,
                )
                raise ExitProcess()
            except CantRegisterBeneficiary as cant_register_beneficiary_exception:
                exception_reason = str(cant_register_beneficiary_exception)
                is_eligible = (isinstance(cant_register_beneficiary_exception, BeneficiaryIsADuplicate),)
                self.reject_user(
                    application_id,
                    exception_reason,
                    preexisting_account,
                    beneficiary_pre_subscription,
                    is_eligible,
                )
                raise ExitProcess()
        except ExitProcess:
            return

        user = self.beneficiary_repository.save(beneficiary_pre_subscription, user=preexisting_account)
        logger.info("User registered from application", extra={"applicationId": application_id, "userId": user.id})

        if preexisting_account is None:
            token = create_reset_password_token(user)
            user_emails.send_activation_email(user=user, token=token)
        else:
            user_emails.send_accepted_as_beneficiary_email(user=user)


class JouveBeneficiaryBackend(BaseBeneficiaryBackend):
    SOURCE = BeneficiaryImportSources.jouve
    SOURCE_ID = jouve_backend.DEFAULT_JOUVE_SOURCE_ID
    beneficiary_repository = BeneficiarySQLRepository()  # TODO: review that class

    def get_data_from_remote(self, application_id) -> dict:
        try:
            return jouve_backend._get_raw_content(application_id)
        except jouve_backend.ApiJouveException as api_jouve_exception:
            logger.error(
                api_jouve_exception.message,
                extra={
                    "route": api_jouve_exception.route,
                    "statusCode": api_jouve_exception.status_code,
                    "applicationId": application_id,
                },
            )
            raise ExitProcess()

    def parse_remote_data(
        self, application_id: int, raw_data: dict, ignore_id_piece_number_field: bool = False
    ) -> BeneficiaryPreSubscription:
        try:
            try:
                jouve_content = jouve_backend.JouveContent(**raw_data)
            except jouve_backend.ValidationError as exc:
                raise jouve_backend.JouveContentValidationError(str(exc), exc.errors)

            if ignore_id_piece_number_field:
                jouve_content.bodyPieceNumber = None

            return jouve_backend.get_subscription_from_content(jouve_content)
        except jouve_backend.JouveContentValidationError as exc:
            logger.error(
                "Validation error when parsing Jouve content: %s",
                exc.message,
                extra={"application_id": application_id, "validation_errors": exc.errors},
            )
            raise ExitProcess()

    def process_result(self, preexisting_account, jouve_content):
        on_jouve_result(preexisting_account, jouve_backend.JouveContent(**jouve_content))


class LegacyDMSBeneficiaryBackend(BaseBeneficiaryBackend):
    SOURCE = BeneficiaryImportSources.demarches_simplifiees
    # beneficiary_repository = BeneficiarySQLRepository()  # TODO: review that class

    def __init__(self, procedure_id: int):
        self.SOURCE_ID = procedure_id

    def get_data_from_remote(self, application_id) -> dict:
        try:
            return get_application_details(application_id, self.SOURCE_ID, settings.DMS_TOKEN)
        except Exception as api_dms_exception:
            logger.error(
                str(api_dms_exception),
                extra={"applicationId": application_id},
            )
            raise ExitProcess()

    def parse_remote_data(
        self, application_id: int, raw_data: dict, ignore_id_piece_number_field: bool = False
    ) -> BeneficiaryPreSubscription:
        try:
            return dms_remote_import.parse_beneficiary_information(**raw_data)
        except dms_remote_import.DMSParsingError as exc:
            # TODO: call dms_remote_immport.process_parsing_error
            logger.error(
                "Validation error when parsing DMS content: %s",
                exc.message,
                extra={
                    "application_id": application_id,
                    "validation_errors": exc.errors,
                    "procedure_id": self.SOURCE_ID,
                },
            )
            raise ExitProcess()

    def process_result(self, preexisting_account, jouve_content):
        on_dms_fraud_check(preexisting_account, jouve_content)
