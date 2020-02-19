from mailjet_rest import Client

from models.feature import FeatureToggle
from scheduled_tasks.decorators import log_cron, cron_context, cron_require_feature
from scripts.send_remedial_emails import send_remedial_emails
from utils.mailing import MAILJET_API_KEY, MAILJET_API_SECRET


@log_cron
@cron_context
@cron_require_feature(FeatureToggle.RESEND_EMAIL_IN_ERROR)
def resend_emails_in_error(app):
    app.mailjet_client = Client(auth=(MAILJET_API_KEY, MAILJET_API_SECRET), version='v3')
    send_remedial_emails()
