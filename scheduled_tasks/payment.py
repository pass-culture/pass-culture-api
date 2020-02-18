import os

from mailjet_rest import Client

from scheduled_tasks.clock import app
from scheduled_tasks.decorators import log_cron
from utils.mailing import MAILJET_API_KEY, MAILJET_API_SECRET, parse_email_addresses


@log_cron
def pc_generate_and_send_payments(payment_message_id: str = None):
    with app.app_context():
        from scripts.payment.batch import generate_and_send_payments
        app.mailjet_client = Client(auth=(MAILJET_API_KEY, MAILJET_API_SECRET), version='v3')
        generate_and_send_payments(payment_message_id)


@log_cron
def pc_send_wallet_balances():
    with app.app_context():
        from scripts.payment.batch import send_wallet_balances
        app.mailjet_client = Client(auth=(MAILJET_API_KEY, MAILJET_API_SECRET), version='v3')
        recipients = parse_email_addresses(os.environ.get('WALLET_BALANCES_RECIPIENTS', None))
        send_wallet_balances(recipients)
