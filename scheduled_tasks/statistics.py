from scheduled_tasks.clock import app
from scheduled_tasks.decorators import log_cron
from scripts.dashboard.write_dashboard import write_dashboard


@log_cron
def pc_write_dashboard():
    with app.app_context():
        write_dashboard()
