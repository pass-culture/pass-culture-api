from mailjet_rest import Client

from scheduled_tasks.clock import app
from scheduled_tasks.decorators import log_cron
from utils.mailing import MAILJET_API_KEY, MAILJET_API_SECRET


@log_cron
def pc_send_final_booking_recaps():
    with app.app_context():
        from scripts.send_final_booking_recaps import send_final_booking_recaps
        app.mailjet_client = Client(auth=(MAILJET_API_KEY, MAILJET_API_SECRET), version='v3')
        send_final_booking_recaps()


@log_cron
def pc_update_booking_used():
    with app.app_context():
        from scripts.update_booking_used import update_booking_used_after_stock_occurrence
        update_booking_used_after_stock_occurrence()
