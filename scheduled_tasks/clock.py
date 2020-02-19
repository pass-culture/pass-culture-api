import os

from apscheduler.schedulers.blocking import BlockingScheduler
from flask import Flask
from sqlalchemy import orm

from models.db import db
from repository.feature_queries import feature_cron_synchronize_allocine_stocks, \
    feature_cron_retrieve_offerers_bank_information, feature_cron_send_remedial_emails, \
    feature_import_beneficiaries_enabled, feature_write_dashboard_enabled, feature_update_booking_used, \
    feature_update_recommendations_view
from scheduled_tasks.booking import pc_update_booking_used
from scheduled_tasks.emails import pc_send_remedial_emails
from scheduled_tasks.provider import pc_retrieve_offerers_bank_information, pc_remote_import_beneficiaries
from scheduled_tasks.recommendation import pc_update_recommendations_view, RECO_VIEW_REFRESH_FREQUENCY
from scheduled_tasks.statistics import pc_write_dashboard
from scheduled_tasks.venue_provider import synchronize_libraires_stocks, pc_synchronize_allocine_stocks

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

    if feature_cron_retrieve_offerers_bank_information():
        scheduler.add_job(pc_retrieve_offerers_bank_information, 'cron',
                          [app],
                          id='retrieve_offerers_bank_information',
                          day='*')

    if feature_cron_synchronize_allocine_stocks():
        scheduler.add_job(pc_synchronize_allocine_stocks, 'cron',
                          [app],
                          id='synchronize_allocine_stocks',
                          day='*', hour='23')

    if feature_cron_send_remedial_emails():
        scheduler.add_job(pc_send_remedial_emails, 'cron',
                          [app],
                          id='send_remedial_emails',
                          minute='*/15')

    if feature_import_beneficiaries_enabled():
        scheduler.add_job(pc_remote_import_beneficiaries, 'cron',
                          [app],
                          id='remote_import_beneficiaries',
                          day='*')

    if feature_write_dashboard_enabled():
        scheduler.add_job(pc_write_dashboard, 'cron',
                          [app],
                          id='pc_write_dashboard',
                          day='*', hour='4')

    if feature_update_booking_used():
        scheduler.add_job(pc_update_booking_used, 'cron',
                          [app],
                          id='pc_update_booking_used',
                          day='*', hour='0')

    if feature_update_recommendations_view():
        scheduler.add_job(pc_update_recommendations_view, 'cron',
                          [app],
                          id='pc_update_recommendations_view',
                          minute=RECO_VIEW_REFRESH_FREQUENCY)

    scheduler.start()
