from datetime import datetime
import logging
from typing import Optional

from lxml.etree import DocumentInvalid

import pcapi.core.bookings.repository as booking_repository
from pcapi.core.offerers.models import Offerer
from pcapi.domain.admin_emails import send_payment_details_email
from pcapi.domain.admin_emails import send_payment_message_email
from pcapi.domain.admin_emails import send_payments_report_emails
from pcapi.domain.admin_emails import send_wallet_balances_email
from pcapi.domain.payments import create_all_payments_details
from pcapi.domain.payments import create_payment_for_booking
from pcapi.domain.payments import filter_out_already_paid_for_bookings
from pcapi.domain.payments import filter_out_bookings_without_cost
from pcapi.domain.payments import generate_file_checksum
from pcapi.domain.payments import generate_message_file
from pcapi.domain.payments import generate_payment_details_csv
from pcapi.domain.payments import generate_payment_message
from pcapi.domain.payments import generate_wallet_balances_csv
from pcapi.domain.payments import group_payments_by_status
from pcapi.domain.payments import keep_only_not_processable_payments
from pcapi.domain.payments import keep_only_pending_payments
from pcapi.domain.payments import validate_message_file_structure
from pcapi.domain.reimbursement import RULES
from pcapi.domain.reimbursement import find_all_booking_reimbursements
from pcapi.models.db import db
from pcapi.models.payment import Payment
from pcapi.models.payment_status import TransactionStatus
from pcapi.repository import payment_queries
from pcapi.repository import repository
from pcapi.repository.user_queries import get_all_users_wallet_balances


logger = logging.getLogger(__name__)
from pcapi.utils.mailing import MailServiceException


def concatenate_payments_with_errors_and_retries(payments: list[Payment]) -> list[Payment]:
    error_payments = payment_queries.find_error_payments()
    retry_payments = payment_queries.find_retry_payments()
    payments = payments + error_payments + retry_payments

    logger.info("[BATCH][PAYMENTS] %i Payments in status ERROR to send", len(error_payments))
    logger.info("[BATCH][PAYMENTS] %i Payments in status RETRY to send", len(retry_payments))
    logger.info("[BATCH][PAYMENTS] %i Payments in total to send", len(payments))

    return payments


def generate_new_payments() -> tuple[list[Payment], list[Payment]]:
    offerers = Offerer.query.all()
    all_payments = []

    for offerer in offerers:
        booking_reimbursements = []
        for venue in offerer.managedVenues:
            final_bookings = booking_repository.find_bookings_eligible_for_payment_for_venue(venue.id)
            booking_reimbursements += find_all_booking_reimbursements(final_bookings, RULES)

        booking_reimbursements_to_pay = filter_out_already_paid_for_bookings(
            filter_out_bookings_without_cost(booking_reimbursements)
        )

        with db.session.no_autoflush:
            payments = list(map(create_payment_for_booking, booking_reimbursements_to_pay))

        if payments:
            repository.save(*payments)
            all_payments.extend(payments)
        logger.info("[BATCH][PAYMENTS] Saved %i payments for offerer : %s", len(payments), offerer.name)

    logger.info("[BATCH][PAYMENTS] Generated %i payments for %i offerers in total", len(all_payments), len(offerers))

    pending_payments = keep_only_pending_payments(all_payments)
    not_processable_payments = keep_only_not_processable_payments(all_payments)
    logger.info("[BATCH][PAYMENTS] %s Payments in status PENDING to send", len(pending_payments))
    return pending_payments, not_processable_payments


def send_transactions(
    payments: list[Payment],
    pass_culture_iban: Optional[str],
    pass_culture_bic: Optional[str],
    pass_culture_remittance_code: Optional[str],
    recipients: list[str],
) -> None:
    if not pass_culture_iban or not pass_culture_bic or not pass_culture_remittance_code:
        raise Exception(
            "[BATCH][PAYMENTS] Missing PASS_CULTURE_IBAN[%s], PASS_CULTURE_BIC[%s] or "
            "PASS_CULTURE_REMITTANCE_CODE[%s] in environment variables"
            % (pass_culture_iban, pass_culture_bic, pass_culture_remittance_code)
        )

    message_name = "passCulture-SCT-%s" % datetime.strftime(datetime.utcnow(), "%Y%m%d-%H%M%S")
    xml_file = generate_message_file(
        payments, pass_culture_iban, pass_culture_bic, message_name, pass_culture_remittance_code
    )

    logger.info("[BATCH][PAYMENTS] Payment message name : %s", message_name)

    try:
        validate_message_file_structure(xml_file)
    except DocumentInvalid as exception:
        for payment in payments:
            payment.setStatus(TransactionStatus.NOT_PROCESSABLE, detail=str(exception))
        repository.save(*payments)
        raise

    checksum = generate_file_checksum(xml_file)
    message = generate_payment_message(message_name, checksum, payments)

    logger.info(
        "[BATCH][PAYMENTS] Sending file with message ID [%s] and checksum [%s]", message.name, message.checksum.hex()
    )
    logger.info("[BATCH][PAYMENTS] Recipients of email : %s", recipients)

    successfully_sent_payments = send_payment_message_email(xml_file, checksum, recipients)
    logger.info("[BATCH][PAYMENTS] Updating status of %d payments", len(payments))
    if successfully_sent_payments:
        for payment in payments:
            payment.setStatus(TransactionStatus.UNDER_REVIEW)
    else:
        for payment in payments:
            payment.setStatus(TransactionStatus.ERROR, detail="Erreur d'envoi à MailJet")
    repository.save(message, *payments)


def send_payments_details(payments: list[Payment], recipients: list[str]) -> None:
    if not recipients:
        raise Exception("[BATCH][PAYMENTS] Missing PASS_CULTURE_PAYMENTS_DETAILS_RECIPIENTS in environment variables")

    if all(map(lambda x: x.currentStatus.status == TransactionStatus.ERROR, payments)):
        logger.warning("[BATCH][PAYMENTS] Not sending payments details as all payments have an ERROR status")
    else:
        details = create_all_payments_details(payments)
        csv = generate_payment_details_csv(details)
        logger.info("[BATCH][PAYMENTS] Sending %s details of %s payments", len(details), len(payments))
        logger.info("[BATCH][PAYMENTS] Recipients of email : %s", recipients)
        try:
            send_payment_details_email(csv, recipients)
        except MailServiceException as exception:
            logger.exception("[BATCH][PAYMENTS] Error while sending payment details email to MailJet: %s", exception)


def send_wallet_balances(recipients: list[str]) -> None:
    if not recipients:
        raise Exception("[BATCH][PAYMENTS] Missing PASS_CULTURE_WALLET_BALANCES_RECIPIENTS in environment variables")

    balances = get_all_users_wallet_balances()
    csv = generate_wallet_balances_csv(balances)
    logger.info("[BATCH][PAYMENTS] Sending %s wallet balances", len(balances))
    logger.info("[BATCH][PAYMENTS] Recipients of email : %s", recipients)
    try:
        send_wallet_balances_email(csv, recipients)
    except MailServiceException as exception:
        logger.exception("[BATCH][PAYMENTS] Error while sending users wallet balances email to MailJet: %s", exception)


def send_payments_report(payments: list[Payment], recipients: list[str]) -> None:
    if not payments:
        logger.info("[BATCH][PAYMENTS] No payments to report to the pass Culture team")
        return

    groups = group_payments_by_status(payments)

    payments_error_details = create_all_payments_details(groups["ERROR"]) if "ERROR" in groups else []
    error_csv = generate_payment_details_csv(payments_error_details)

    payments_not_processable_details = (
        create_all_payments_details(groups["NOT_PROCESSABLE"]) if "NOT_PROCESSABLE" in groups else []
    )
    not_processable_csv = generate_payment_details_csv(payments_not_processable_details)

    logger.info(
        "[BATCH][PAYMENTS] Sending report on %s payment in ERROR and %s payment NOT_PROCESSABLE",
        len(payments_error_details),
        len(payments_not_processable_details),
    )
    logger.info("[BATCH][PAYMENTS] Recipients of email : %s", recipients)

    try:
        send_payments_report_emails(not_processable_csv, error_csv, groups, recipients)
    except MailServiceException as exception:
        logger.exception("[BATCH][PAYMENTS] Error while sending payments reports to MailJet: %s", exception)


def set_not_processable_payments_with_bank_information_to_retry() -> None:
    payments_to_retry = payment_queries.find_not_processable_with_bank_information()
    for payment in payments_to_retry:
        payment_bank_information_is_on_venue = (
            payment.booking.stock.offer.venue.bic and payment.booking.stock.offer.venue.bic
        )
        payment_bank_information_is_on_offerer = (
            payment.booking.stock.offer.venue.managingOfferer.bic
            and payment.booking.stock.offer.venue.managingOfferer.bic
        )
        if payment_bank_information_is_on_venue:
            payment.bic = payment.booking.stock.offer.venue.bic
            payment.iban = payment.booking.stock.offer.venue.iban
        elif payment_bank_information_is_on_offerer:
            payment.bic = payment.booking.stock.offer.venue.managingOfferer.bic
            payment.iban = payment.booking.stock.offer.venue.managingOfferer.iban
        payment.setStatus(TransactionStatus.RETRY)
    repository.save(*payments_to_retry)
