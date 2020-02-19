from models.feature import FeatureToggle
from scheduled_tasks.decorators import log_cron, cron_context, cron_require_feature
from scripts.update_booking_used import update_booking_used_after_stock_occurrence


@log_cron
@cron_context
@cron_require_feature(FeatureToggle.UPDATE_BOOKING_USED)
def update_booking_used(app):
    update_booking_used_after_stock_occurrence()
