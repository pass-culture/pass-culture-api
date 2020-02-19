from scheduled_tasks.decorators import log_cron, cron_context
from scripts.dashboard.write_dashboard import write_dashboard


@log_cron
@cron_context
def write_statistics_dashboard(app):
    write_dashboard()
