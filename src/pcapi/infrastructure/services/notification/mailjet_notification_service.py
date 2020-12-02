from datetime import datetime
import os
from typing import Callable

from pcapi.core.bookings.models import Booking
from pcapi.core.bookings.models import BookingCancellationReasons
from pcapi.domain.beneficiary_contact.beneficiary_contact import BeneficiaryContact
from pcapi.domain.beneficiary_contact.beneficiary_contact_exceptions import AddNewBeneficiaryContactException
from pcapi.domain.services.notification.notification_service import NotificationService
from pcapi.domain.user_emails import send_booking_cancellation_emails_to_user_and_offerer
from pcapi.domain.user_emails import send_booking_confirmation_email_to_beneficiary
from pcapi.domain.user_emails import send_booking_recap_emails
from pcapi.utils.logger import logger
from pcapi.utils.mailing import MailServiceException
from pcapi.utils.mailing import add_contact_informations
from pcapi.utils.mailing import add_contact_to_list
from pcapi.utils.mailing import create_contact
from pcapi.utils.mailing import send_raw_email


class MailjetNotificationService(NotificationService):
    def send_booking_recap(self, booking: Booking) -> None:
        try:
            send_booking_recap_emails(booking, send_raw_email)
        except MailServiceException as error:
            logger.exception("Mail service failure", error)

    def send_booking_confirmation_to_beneficiary(self, booking: Booking) -> None:
        try:
            send_booking_confirmation_email_to_beneficiary(booking, send_raw_email)
        except MailServiceException as error:
            logger.exception("Mail service failure", error)

    def send_booking_cancellation_emails_to_user_and_offerer(
        self,
        booking: Booking,
        reason: BookingCancellationReasons,
        send_email: Callable[..., bool],
    ):
        try:
            send_booking_cancellation_emails_to_user_and_offerer(booking, reason, send_raw_email)
        except MailServiceException as error:
            logger.exception("Mail service failure", error)

    def create_mailing_contact(self, beneficiary_contact: BeneficiaryContact) -> None:
        creation_response = create_contact(beneficiary_contact.email)

        status_code = creation_response.status_code
        if status_code != 201 and status_code != 400:
            raise AddNewBeneficiaryContactException("mailjet", creation_response.reason)

        date_of_birth = datetime.fromisoformat(beneficiary_contact.date_of_birth)
        date_of_birth_timestamp = int(datetime(date_of_birth.year, date_of_birth.month, date_of_birth.day).timestamp())
        update_response = add_contact_informations(
            beneficiary_contact.email, date_of_birth_timestamp, beneficiary_contact.department_code
        )

        status_code = update_response.status_code
        if status_code != 200 and status_code != 400:
            raise AddNewBeneficiaryContactException("mailjet", update_response.reason)

    def add_contact_to_eligible_soon_list(self, beneficiary_contact: BeneficiaryContact) -> None:
        list_id = os.environ.get("MAILJET_NOT_YET_ELIGIBLE_LIST_ID")
        add_to_list_response = add_contact_to_list(beneficiary_contact.email, list_id)

        status_code = add_to_list_response.status_code
        if status_code != 201 and status_code != 400:
            raise AddNewBeneficiaryContactException("mailjet", add_to_list_response.reason)
