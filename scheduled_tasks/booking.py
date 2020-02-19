from scheduled_tasks.decorators import log_cron, cron_context


@log_cron
@cron_context
def pc_update_booking_used(app):
    from scripts.update_booking_used import update_booking_used_after_stock_occurrence
    update_booking_used_after_stock_occurrence()
