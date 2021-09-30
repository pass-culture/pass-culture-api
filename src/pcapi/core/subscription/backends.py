import logging
from typing import Any
from typing import Optional
from typing import Union

from pcapi.connectors.beneficiaries import jouve_backend
from pcapi.core.fraud.api import on_jouve_result
from pcapi.core.subscription.models import BeneficiaryPreSubscription
from pcapi.core.users.api import create_reset_password_token
from pcapi.core.users.models import User
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


logger = logging.getLogger(__name__)


class ExitProcess(Exception):
    pass


BeneficiaryContent = Union[jouve_backend.JouveContent]


class BaseBeneficiaryBackend:
    SOURCE: Optional[BeneficiaryImportSources] = None
    SOURCE_ID: Optional[int] = None
    beneficiary_repository = BeneficiarySQLRepository()

    def get_data_from_remote(self, application_id: int) -> BeneficiaryContent:
        raise NotImplementedError()

    def parse_remote_data(
        self, application_id: int, content: BeneficiaryContent, ignore_id_piece_number_field: bool = False
    ) -> Any:
        raise NotImplementedError()

    def process_result(self, preexisting_account: User, content: BeneficiaryContent) -> None:
        raise NotImplementedError()

    def no_preexisting_account_error(
        self, application_id: int, beneficiary_pre_subscription: BeneficiaryPreSubscription
    ) -> None:
        assert self.SOURCE
        save_beneficiary_import_with_status(
            ImportStatus.ERROR,
            application_id,
            source=self.SOURCE,
            source_id=self.SOURCE_ID,
            detail=f"Aucun utilisateur trouvé pour l'email {beneficiary_pre_subscription.email}",
        )
        raise ExitProcess()

    def reject_user(
        self,
        application_id: int,
        reason: str,
        preexisting_account: User,
        beneficiary_pre_subscription: BeneficiaryPreSubscription,
        is_eligible: bool,
    ) -> None:
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
    ) -> None:
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
            content = self.get_data_from_remote(application_id)
            beneficiary_pre_subscription = self.parse_remote_data(
                application_id, content, ignore_id_piece_number_field=ignore_id_piece_number_field
            )

            preexisting_account = find_user_by_email(beneficiary_pre_subscription.email)
            if not preexisting_account:
                self.no_preexisting_account_error(application_id, beneficiary_pre_subscription)

            try:
                self.process_result(preexisting_account, content)
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
                is_eligible = isinstance(cant_register_beneficiary_exception, BeneficiaryIsADuplicate)
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

    def get_data_from_remote(self, application_id: int) -> jouve_backend.JouveContent:
        try:
            raw_content = jouve_backend._get_raw_content(str(application_id))
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

        try:
            return jouve_backend.JouveContent(**raw_content)
        except jouve_backend.JouveContentValidationError as exc:
            logger.error(
                "Validation error when parsing Jouve content: %s",
                exc.message,
                extra={"application_id": application_id, "validation_errors": exc.errors},
            )
            raise ExitProcess()

    def parse_remote_data(
        self, application_id: int, content: jouve_backend.JouveContent, ignore_id_piece_number_field: bool = False
    ) -> BeneficiaryPreSubscription:
        if ignore_id_piece_number_field:
            content.bodyPieceNumber = None
        return jouve_backend.get_subscription_from_content(content)

    def process_result(self, preexisting_account: User, content: jouve_backend.JouveContent) -> None:
        on_jouve_result(preexisting_account, content)
