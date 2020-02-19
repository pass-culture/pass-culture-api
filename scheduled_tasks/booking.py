from scheduled_tasks import clock
from scheduled_tasks.decorators import log_cron


@log_cron
def pc_update_booking_used():
    with clock.app.app_context():
        from scripts.update_booking_used import update_booking_used_after_stock_occurrence
        update_booking_used_after_stock_occurrence()
