from scheduled_tasks.decorators import log_cron, cron_context
from scripts.dashboard.write_dashboard import write_dashboard


@log_cron
@cron_context
def pc_write_dashboard(app):
    write_dashboard()
