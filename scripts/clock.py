import os
import subprocess
from io import StringIO

from apscheduler.schedulers.blocking import BlockingScheduler
from flask import Flask
from mailjet_rest import Client
from sqlalchemy import orm

from models.db import db
from repository.feature_queries import feature_cron_send_final_booking_recaps_enabled, \
    feature_cron_generate_and_send_payments, \
    feature_cron_retrieve_offerers_bank_information,\
    feature_cron_send_remedial_emails,\
    feature_write_dashboard_enabled, \
    feature_update_booking_used,\
    feature_delete_all_unread_recommendations_older_than_one_week_enabled, \
    feature_cron_retrieve_bank_information_for_venue_without_siret, \
    feature_cron_send_wallet_balances, \
    feature_import_beneficiaries_enabled, \
    feature_cron_synchronize_titelive_things,\
    feature_cron_synchronize_titelive_descriptions, \
    feature_cron_synchronize_titelive_thumbs,\
    feature_cron_synchronize_titelive_stocks
from repository.provider_queries import get_provider_by_local_class
from repository.recommendation_queries import delete_all_unread_recommendations_older_than_one_week
from repository.user_queries import find_most_recent_beneficiary_creation_date
from scripts.beneficiary import remote_import
from scripts.dashboard.write_dashboard import write_dashboard
from utils.config import API_ROOT_PATH
from utils.logger import logger
from utils.mailing import MAILJET_API_KEY, MAILJET_API_SECRET, parse_email_addresses

app = Flask(__name__, template_folder='../templates')
app.config['SQLALCHEMY_DATABASE_URI'] = os.environ.get('DATABASE_URL')
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
app.config['DEBUG'] = True
db.init_app(app)

TITELIVE_STOCKS_PROVIDER_NAME = "TiteLiveStocks"


def pc_send_final_booking_recaps():
    print("[BATCH] Cron send_final_booking_recaps: START")
    with app.app_context():
        from scripts.send_final_booking_recaps import send_final_booking_recaps
        app.mailjet_client = Client(auth=(MAILJET_API_KEY, MAILJET_API_SECRET), version='v3')
        send_final_booking_recaps()

    print("[BATCH] Cron send_final_booking_recaps: END")


def pc_generate_and_send_payments(payment_message_id: str = None):
    logger.info("[BATCH][PAYMENTS] Cron generate_and_send_payments: START")

    with app.app_context():
        from scripts.payment.batch import generate_and_send_payments
        app.mailjet_client = Client(auth=(MAILJET_API_KEY, MAILJET_API_SECRET), version='v3')
        generate_and_send_payments(payment_message_id)

    logger.info("[BATCH][PAYMENTS] Cron generate_and_send_payments: END")


def pc_update_booking_used():
    logger.info("[BATCH][BOOKINGS] Cron update_booking_used: START")

    with app.app_context():
        from scripts.update_booking_used import update_booking_used_after_stock_occurrence
        update_booking_used_after_stock_occurrence()

    logger.info("[BATCH][BOOKINGS] Cron update_booking_used: END")


def pc_send_wallet_balances():
    logger.info("[BATCH] Cron send_wallet_balances: START")

    with app.app_context():
        from scripts.payment.batch import send_wallet_balances
        app.mailjet_client = Client(auth=(MAILJET_API_KEY, MAILJET_API_SECRET), version='v3')
        recipients = parse_email_addresses(os.environ.get('WALLET_BALANCES_RECIPIENTS', None))
        send_wallet_balances(recipients)

    logger.info("[BATCH] Cron send_wallet_balances: END")


def pc_synchronize_titelive_things():
    logger.info("[BATCH][TITELIVE THINGS] Cron synchronize_titelive_things: START")
    with app.app_context():
        process = subprocess.Popen('PYTHONPATH="." python scripts/pc.py update_providables'
                                   + ' --provider TiteLiveThings',
                                   shell=True,
                                   cwd=API_ROOT_PATH)
        output, error = process.communicate()
        logger.info(StringIO(output))
        logger.info(StringIO(error))
    logger.info("[BATCH][TITELIVE THINGS] Cron synchronize_titelive_things: END")


def pc_synchronize_titelive_descriptions():
    logger.info("[BATCH][TITELIVE DESCRIPTIONS] Cron synchronize_titelive_descriptions: START")
    with app.app_context():
        process = subprocess.Popen('PYTHONPATH="." python scripts/pc.py update_providables'
                                   + ' --provider TiteLiveThingDescriptions',
                                   shell=True,
                                   cwd=API_ROOT_PATH)
        output, error = process.communicate()
        logger.info(StringIO(output))
        logger.info(StringIO(error))
    logger.info("[BATCH][TITELIVE DESCRIPTIONS] Cron synchronize_titelive_descriptions: END")


def pc_synchronize_titelive_thumbs():
    logger.info("[BATCH][TITELIVE THUMBS] Cron synchronize_titelive_thumbs: START")
    with app.app_context():
        process = subprocess.Popen('PYTHONPATH="." python scripts/pc.py update_providables'
                                   + ' --provider TiteLiveThingThumbs',
                                   shell=True,
                                   cwd=API_ROOT_PATH)
        output, error = process.communicate()
        logger.info(StringIO(output))
        logger.info(StringIO(error))
    logger.info("[BATCH][TITELIVE THUMBS] Cron synchronize_titelive_thumbs: END")


def pc_synchronize_titelive_stocks():
    logger.info("[BATCH][TITELIVE STOCKS] Cron synchronize_titelive_stocks: START")
    with app.app_context():
        titelive_stocks_provider_id = get_provider_by_local_class(TITELIVE_STOCKS_PROVIDER_NAME).id
        process = subprocess.Popen('PYTHONPATH="." python scripts/pc.py update_providables_by_provider_id --provider-id '
                         + str(titelive_stocks_provider_id),
                         shell=True,
                         cwd=API_ROOT_PATH)
        output, error = process.communicate()
        logger.info(StringIO(output))
        logger.info(StringIO(error))
    logger.info("[BATCH][TITELIVE STOCKS] Cron synchronize_titelive_stocks: END")


def pc_retrieve_offerers_bank_information():
    logger.info("[BATCH][BANK INFORMATION] Cron retrieve_offerers_bank_information: START")
    with app.app_context():
        process = subprocess.Popen('PYTHONPATH="." python scripts/pc.py update_providables'
                                   + ' --provider BankInformationProvider',
                                   shell=True,
                                   cwd=API_ROOT_PATH)
        output, error = process.communicate()
        logger.info(StringIO(output))
        logger.info(StringIO(error))
    logger.info("[BATCH][BANK INFORMATION] Cron retrieve_offerers_bank_information: END")


def pc_retrieve_bank_information_for_venue_without_siret():
    logger.info("[BATCH][BANK INFORMATION] Cron retrieve_bank_information_venue_without_siret: START")
    with app.app_context():
        process = subprocess.Popen('PYTHONPATH="." python scripts/pc.py update_providables'
                                   + ' --provider VenueWithoutSIRETBankInformationProvider',
                                   shell=True,
                                   cwd=API_ROOT_PATH)
        output, error = process.communicate()
        logger.info(StringIO(output))
    logger.info("[BATCH][BANK INFORMATION] Cron retrieve_bank_information_venue_without_siret: END")


def pc_send_remedial_emails():
    logger.info("[BATCH][REMEDIAL EMAILS] Cron send_remedial_emails: START")
    with app.app_context():
        from scripts.send_remedial_emails import send_remedial_emails
        app.mailjet_client = Client(auth=(MAILJET_API_KEY, MAILJET_API_SECRET), version='v3')
        send_remedial_emails()
    logger.info("[BATCH][REMEDIAL EMAILS] Cron send_remedial_emails: END")


def pc_remote_import_beneficiaries():
    logger.info("[BATCH][REMOTE IMPORT BENEFICIARIES] Cron remote_import_beneficiaries: START")
    with app.app_context():
        app.mailjet_client = Client(auth=(MAILJET_API_KEY, MAILJET_API_SECRET), version='v3')
        import_from_date = find_most_recent_beneficiary_creation_date()
        remote_import.run(import_from_date)
    logger.info("[BATCH][REMOTE IMPORT BENEFICIARIES] Cron remote_import_beneficiaries: END")


def pc_write_dashboard():
    logger.info("[BATCH][WRITE DASHBOARD] Cron write_dashboard: START")
    with app.app_context():
        write_dashboard()
    logger.info("[BATCH][WRITE DASHBOARD] Cron write_dashboard: END")


def pc_delete_all_unread_recommendations_older_than_one_week():
    logger.info("[BATCH] Cron delete_all_unread_recommendations_older_than_one_week: START")
    with app.app_context():
        delete_all_unread_recommendations_older_than_one_week()
    logger.info("[BATCH] Cron delete_all_unread_recommendations_older_than_one_week: END")


if __name__ == '__main__':
    orm.configure_mappers()
    scheduler = BlockingScheduler()

    if feature_cron_send_final_booking_recaps_enabled():
        scheduler.add_job(pc_send_final_booking_recaps, 'cron', id='send_final_booking_recaps', day='*')

    if feature_cron_generate_and_send_payments():
        scheduler.add_job(pc_generate_and_send_payments, 'cron', id='generate_and_send_payments', day='1,15')

    if feature_cron_send_wallet_balances():
        scheduler.add_job(pc_send_wallet_balances, 'cron', id='send_wallet_balances', day='1-5')

    if feature_cron_retrieve_offerers_bank_information():
        scheduler.add_job(pc_retrieve_offerers_bank_information, 'cron', id='retrieve_offerers_bank_information',
                          day='*')

    if feature_cron_retrieve_bank_information_for_venue_without_siret():
        scheduler.add_job(pc_retrieve_bank_information_for_venue_without_siret, 'cron',
                          id='retrieve_bank_information_venue_without_siret',
                          day='*')

    if feature_cron_synchronize_titelive_things():
        scheduler.add_job(pc_synchronize_titelive_things, 'cron', id='synchronize_titelive_things',
                          day='*', hour='1')

    if feature_cron_synchronize_titelive_descriptions():
        scheduler.add_job(pc_synchronize_titelive_descriptions, 'cron', id='synchronize_titelive_descriptions',
                          day='*', hour='2')

    if feature_cron_synchronize_titelive_thumbs():
        scheduler.add_job(pc_synchronize_titelive_thumbs, 'cron', id='synchronize_titelive_thumbs',
                          day='*', hour='3')

    if feature_cron_synchronize_titelive_stocks():
        scheduler.add_job(pc_synchronize_titelive_stocks, 'cron', id='synchronize_titelive_stocks',
                          day='*', hour='4')

    if feature_cron_send_remedial_emails():
        scheduler.add_job(pc_send_remedial_emails, 'cron', id='send_remedial_emails', minute='*/15')

    if feature_import_beneficiaries_enabled():
        scheduler.add_job(pc_remote_import_beneficiaries, 'cron', id='remote_import_beneficiaries', day='*')

    if feature_write_dashboard_enabled():
        scheduler.add_job(pc_write_dashboard, 'cron', id='pc_write_dashboard', day_of_week='mon', hour='4')

    if feature_update_booking_used():
        scheduler.add_job(pc_update_booking_used, 'cron', id='pc_update_booking_used', day='*', hour='0')

    if feature_delete_all_unread_recommendations_older_than_one_week_enabled():
        scheduler.add_job(pc_delete_all_unread_recommendations_older_than_one_week,
                          'cron',
                          id='pc_delete_all_unread_recommendations_older_than_one_week',
                          day_of_week='mon', hour='23')

    scheduler.start()
