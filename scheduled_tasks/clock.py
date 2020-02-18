import os

from apscheduler.schedulers.blocking import BlockingScheduler
from flask import Flask
from sqlalchemy import orm

from models.db import db
from repository.feature_queries import feature_cron_send_final_booking_recaps_enabled, \
    feature_cron_generate_and_send_payments, \
    feature_cron_retrieve_offerers_bank_information, \
    feature_cron_send_remedial_emails, \
    feature_write_dashboard_enabled, \
    feature_update_booking_used, \
    feature_delete_all_unread_recommendations_older_than_one_week_enabled, \
    feature_cron_send_wallet_balances, \
    feature_import_beneficiaries_enabled, \
    feature_cron_synchronize_allocine_stocks, \
    feature_update_recommendations_view
from scheduled_tasks.booking import pc_send_final_booking_recaps, pc_update_booking_used
from scheduled_tasks.emails import pc_send_remedial_emails
from scheduled_tasks.payment import pc_generate_and_send_payments, pc_send_wallet_balances
from scheduled_tasks.provider import pc_retrieve_offerers_bank_information, pc_remote_import_beneficiaries
from scheduled_tasks.recommendation import pc_delete_useless_recommendations, pc_update_recommendations_view, \
    RECO_VIEW_REFRESH_FREQUENCY
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

    scheduler.add_job(synchronize_libraires_stocks(app), 'cron', id='synchronize_libraire_stocks', day='*', hour='21')

    if feature_cron_send_final_booking_recaps_enabled():
        scheduler.add_job(pc_send_final_booking_recaps, 'cron', id='send_final_booking_recaps', day='*')

    if feature_cron_generate_and_send_payments():
        scheduler.add_job(pc_generate_and_send_payments, 'cron', id='generate_and_send_payments', day='1,15')

    if feature_cron_send_wallet_balances():
        scheduler.add_job(pc_send_wallet_balances, 'cron', id='send_wallet_balances', day='1-5')

    if feature_cron_retrieve_offerers_bank_information():
        scheduler.add_job(pc_retrieve_offerers_bank_information, 'cron', id='retrieve_offerers_bank_information',
                          day='*')

    if feature_cron_synchronize_allocine_stocks():
        scheduler.add_job(pc_synchronize_allocine_stocks, 'cron', id='synchronize_allocine_stocks',
                          day='*', hour='23')

    if feature_cron_send_remedial_emails():
        scheduler.add_job(pc_send_remedial_emails, 'cron', id='send_remedial_emails', minute='*/15')

    if feature_import_beneficiaries_enabled():
        scheduler.add_job(pc_remote_import_beneficiaries, 'cron', id='remote_import_beneficiaries', day='*')

    if feature_write_dashboard_enabled():
        scheduler.add_job(pc_write_dashboard, 'cron', id='pc_write_dashboard', day='*', hour='4')

    if feature_update_booking_used():
        scheduler.add_job(pc_update_booking_used, 'cron', id='pc_update_booking_used', day='*', hour='0')

    if feature_delete_all_unread_recommendations_older_than_one_week_enabled():
        scheduler.add_job(pc_delete_useless_recommendations,
                          'cron',
                          id='pc_delete_useless_recommendations',
                          day_of_week='mon', hour='23')

    if feature_update_recommendations_view():
        scheduler.add_job(pc_update_recommendations_view, 'cron', id='pc_update_recommendations_view',
                          minute=RECO_VIEW_REFRESH_FREQUENCY)

    scheduler.start()
