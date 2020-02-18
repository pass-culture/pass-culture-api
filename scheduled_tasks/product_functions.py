import os

from mailjet_rest import Client

from models import DiscoveryView
from repository.recommendation_queries import delete_useless_recommendations
from scheduled_tasks.clock import app
from scheduled_tasks.decorators import log_cron
from scripts.dashboard.write_dashboard import write_dashboard
from utils.mailing import MAILJET_API_KEY, MAILJET_API_SECRET, parse_email_addresses


@log_cron
def pc_send_final_booking_recaps():
    with app.app_context():
        from scripts.send_final_booking_recaps import send_final_booking_recaps
        app.mailjet_client = Client(auth=(MAILJET_API_KEY, MAILJET_API_SECRET), version='v3')
        send_final_booking_recaps()


@log_cron
def pc_generate_and_send_payments(payment_message_id: str = None):
    with app.app_context():
        from scripts.payment.batch import generate_and_send_payments
        app.mailjet_client = Client(auth=(MAILJET_API_KEY, MAILJET_API_SECRET), version='v3')
        generate_and_send_payments(payment_message_id)


@log_cron
def pc_update_booking_used():
    with app.app_context():
        from scripts.update_booking_used import update_booking_used_after_stock_occurrence
        update_booking_used_after_stock_occurrence()


@log_cron
def pc_send_wallet_balances():
    with app.app_context():
        from scripts.payment.batch import send_wallet_balances
        app.mailjet_client = Client(auth=(MAILJET_API_KEY, MAILJET_API_SECRET), version='v3')
        recipients = parse_email_addresses(os.environ.get('WALLET_BALANCES_RECIPIENTS', None))
        send_wallet_balances(recipients)


@log_cron
def pc_send_remedial_emails():
    with app.app_context():
        from scripts.send_remedial_emails import send_remedial_emails
        app.mailjet_client = Client(auth=(MAILJET_API_KEY, MAILJET_API_SECRET), version='v3')
        send_remedial_emails()


@log_cron
def pc_write_dashboard():
    with app.app_context():
        write_dashboard()


@log_cron
def pc_delete_useless_recommendations():
    with app.app_context():
        delete_useless_recommendations()


@log_cron
def pc_update_recommendations_view():
    with app.app_context():
        DiscoveryView.refresh()


RECO_VIEW_REFRESH_FREQUENCY = os.environ.get('RECO_VIEW_REFRESH_FREQUENCY', '*')