import os
from datetime import datetime
from typing import List

from flask import current_app as app

from domain.admin_emails import send_payment_transaction_email, send_payment_details_email, send_wallet_balances_email, \
    send_payments_report_emails
from domain.payments import filter_out_already_paid_for_bookings, create_payment_for_booking, generate_transaction_file, \
    validate_transaction_file_structure, create_all_payments_details, generate_payment_details_csv, \
    generate_wallet_balances_csv, \
    generate_payment_transaction, generate_file_checksum, group_payments_by_status, filter_out_cost_free_bookings, \
    keep_pending_payments
from domain.reimbursement import find_all_booking_reimbursement
from models import Offerer, PcObject
from models.payment import Payment
from models.payment_status import TransactionStatus
from repository import payment_queries
from repository.booking_queries import find_final_offerer_bookings
from repository.user_queries import get_all_users_wallet_balances
from utils.logger import logger
from utils.mailing import MailServiceException

PASS_CULTURE_IBAN = os.environ.get('PASS_CULTURE_IBAN', None)
PASS_CULTURE_BIC = os.environ.get('PASS_CULTURE_BIC', None)
PASS_CULTURE_REMITTANCE_CODE = os.environ.get('PASS_CULTURE_REMITTANCE_CODE', None)
PAYMENTS_DETAILS_RECIPIENTS = os.environ.get('PAYMENTS_DETAILS_RECIPIENTS', None)
WALLET_BALANCES_RECIPIENTS = os.environ.get('WALLET_BALANCES_RECIPIENTS', None)


def generate_and_send_payments():
    payments = collect_payments()

    try:
        send_transactions(payments, PASS_CULTURE_IBAN, PASS_CULTURE_BIC, PASS_CULTURE_REMITTANCE_CODE)
        send_payments_report(payments)
        send_payments_details(payments, PAYMENTS_DETAILS_RECIPIENTS)
        send_wallet_balances(WALLET_BALANCES_RECIPIENTS)
    except Exception as e:
        logger.error('[BATCH][PAYMENTS] generate_and_send_payments', e)


def collect_payments() -> List[Payment]:
    new_payments = generate_new_payments()
    pending_payments = keep_pending_payments(new_payments)
    error_payments = payment_queries.find_error_payments()
    payments = pending_payments + error_payments
    logger.info('[BATCH][PAYMENTS] %s Payments in status PENDING to send' % len(pending_payments))
    logger.info('[BATCH][PAYMENTS] %s Payments in status ERROR to send' % len(error_payments))
    logger.info('[BATCH][PAYMENTS] %s Payments in total to send' % len(payments))
    return payments


def generate_new_payments() -> List[Payment]:
    offerers = Offerer.query.all()
    logger.info('[BATCH][PAYMENTS] Generating payments for %s Offerers' % len(offerers))
    all_payments = []

    for offerer in offerers:
        logger.info('[BATCH][PAYMENTS] Generating payments for Offerer : %s' % offerer.name)

        final_offerer_bookings = find_final_offerer_bookings(offerer.id)
        booking_reimbursements = find_all_booking_reimbursement(final_offerer_bookings)
        booking_reimbursements_to_pay = filter_out_already_paid_for_bookings(
            filter_out_cost_free_bookings(booking_reimbursements)
        )
        payments = list(map(create_payment_for_booking, booking_reimbursements_to_pay))

        if payments:
            PcObject.check_and_save(*payments)
            all_payments.extend(payments)
            logger.info('[BATCH][PAYMENTS] Saved %s payments for Offerer : %s' % (len(payments), offerer.name))
        else:
            logger.info('[BATCH][PAYMENTS] No payments to save for Offerer : %s' % offerer.name)

    logger.info('[BATCH][PAYMENTS] Generated %s payments in total' % len(all_payments))
    return all_payments


def send_transactions(payments: List[Payment], pass_culture_iban: str, pass_culture_bic: str,
                      pass_culture_remittance_code: str) -> None:
    if not pass_culture_iban or not pass_culture_bic or not pass_culture_remittance_code:
        logger.error(
            '[BATCH][PAYMENTS] Missing PASS_CULTURE_IBAN[%s], PASS_CULTURE_BIC[%s] or PASS_CULTURE_REMITTANCE_CODE[%s] in environment variables' % (
                pass_culture_iban, pass_culture_bic, pass_culture_remittance_code))
    else:
        message_id = 'passCulture-SCT-%s' % datetime.strftime(datetime.utcnow(), "%Y%m%d-%H%M%S")
        xml_file = generate_transaction_file(payments, pass_culture_iban, pass_culture_bic, message_id,
                                             pass_culture_remittance_code)
        validate_transaction_file_structure(xml_file)
        checksum = generate_file_checksum(xml_file)
        transaction = generate_payment_transaction(message_id, checksum, payments)

        try:
            send_payment_transaction_email(xml_file, checksum, app.mailjet_client.send.create)
        except MailServiceException as e:
            logger.error('[BATCH][PAYMENTS] Error while sending payment transaction email to MailJet', e)
            for payment in payments:
                payment.setStatus(TransactionStatus.ERROR, detail="Erreur d'envoi à MailJet")
        else:
            for payment in payments:
                payment.setStatus(TransactionStatus.SENT)
        finally:
            PcObject.check_and_save(transaction, *payments)


def send_payments_details(payments: List[Payment], recipients: str) -> None:
    if not recipients:
        logger.error('[BATCH][PAYMENTS] Missing PASS_CULTURE_PAYMENTS_DETAILS_RECIPIENTS in environment variables')
    else:
        details = create_all_payments_details(payments)
        csv = generate_payment_details_csv(details)
        try:
            send_payment_details_email(csv, recipients, app.mailjet_client.send.create)
        except MailServiceException as e:
            logger.error('[BATCH][PAYMENTS] Error while sending payment details email to MailJet', e)


def send_wallet_balances(recipients: str) -> None:
    if not recipients:
        logger.error('[BATCH][PAYMENTS] Missing PASS_CULTURE_WALLET_BALANCES_RECIPIENTS in environment variables')
    else:
        balances = get_all_users_wallet_balances()
        csv = generate_wallet_balances_csv(balances)
        try:
            send_wallet_balances_email(csv, recipients, app.mailjet_client.send.create)
        except MailServiceException as e:
            logger.error('[BATCH][PAYMENTS] Error while sending users wallet balances email to MailJet', e)


def send_payments_report(payments: List[Payment]) -> None:
    if payments:
        groups = group_payments_by_status(payments)

        payments_error_details = create_all_payments_details(groups['ERROR']) if 'ERROR' in groups else []
        error_csv = generate_payment_details_csv(payments_error_details)

        payments_not_processable_details = create_all_payments_details(
            groups['NOT_PROCESSABLE']) if 'NOT_PROCESSABLE' in groups else []
        not_processable_csv = generate_payment_details_csv(payments_not_processable_details)

        try:
            send_payments_report_emails(not_processable_csv, error_csv, groups, app.mailjet_client.send.create)
        except MailServiceException as e:
            logger.error('[BATCH][PAYMENTS] Error while sending payments reports to MailJet', e)
    else:
        logger.info('[BATCH][PAYMENTS] No payments to report to the pass Culture team')
