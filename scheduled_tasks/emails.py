from mailjet_rest import Client

from scheduled_tasks.clock import app
from scheduled_tasks.decorators import log_cron
from utils.mailing import MAILJET_API_KEY, MAILJET_API_SECRET


@log_cron
def pc_send_remedial_emails():
    with app.app_context():
        from scripts.send_remedial_emails import send_remedial_emails
        app.mailjet_client = Client(auth=(MAILJET_API_KEY, MAILJET_API_SECRET), version='v3')
        send_remedial_emails()
