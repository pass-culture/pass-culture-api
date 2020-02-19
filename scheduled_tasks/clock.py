import os

from apscheduler.schedulers.blocking import BlockingScheduler
from flask import Flask
from sqlalchemy import orm

from models.db import db
from repository.feature_queries import feature_write_dashboard_enabled
from scheduled_tasks.booking import update_booking_used
from scheduled_tasks.emails import resend_emails_in_error
from scheduled_tasks.provider import retrieve_offerers_bank_information, remote_import_beneficiaries
from scheduled_tasks.recommendation import update_discovery_view, RECO_VIEW_REFRESH_FREQUENCY
from scheduled_tasks.statistics import write_statistics_dashboard
from scheduled_tasks.venue_provider import synchronize_libraires_stocks, synchronize_allocine_stocks

app = Flask(__name__, template_folder='../templates')
app.config['SQLALCHEMY_DATABASE_URI'] = os.environ.get('DATABASE_URL')
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
app.config['DEBUG'] = True
db.init_app(app)

if __name__ == '__main__':
    orm.configure_mappers()
    scheduler = BlockingScheduler()

    scheduler.add_job(synchronize_libraires_stocks, 'cron',
                      [app],
                      id='synchronize_libraires_stocks',
                      day='*', hour='22')

    scheduler.add_job(retrieve_offerers_bank_information, 'cron',
                      [app],
                      id='retrieve_offerers_bank_information',
                      day='*')

    scheduler.add_job(synchronize_allocine_stocks, 'cron',
                      [app],
                      id='synchronize_allocine_stocks',
                      day='*', hour='23')

    scheduler.add_job(resend_emails_in_error, 'cron',
                      [app],
                      id='send_remedial_emails',
                      minute='*/15')

    scheduler.add_job(remote_import_beneficiaries, 'cron',
                      [app],
                      id='remote_import_beneficiaries',
                      day='*')

    if feature_write_dashboard_enabled():
        scheduler.add_job(write_statistics_dashboard, 'cron',
                          [app],
                          id='pc_write_dashboard',
                          day='*', hour='4')

    scheduler.add_job(update_booking_used, 'cron',
                      [app],
                      id='pc_update_booking_used',
                      day='*', hour='0')

    scheduler.add_job(update_discovery_view, 'cron',
                      [app],
                      id='pc_update_recommendations_view',
                      minute=RECO_VIEW_REFRESH_FREQUENCY)

    scheduler.start()
