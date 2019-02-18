""" clock """
import os
import subprocess
from apscheduler.schedulers.blocking import BlockingScheduler
from flask import Flask
from io import StringIO
from mailjet_rest import Client

from models.db import db
from repository.features import feature_cron_send_final_booking_recaps_enabled, feature_cron_generate_and_send_payments, \
    feature_cron_retrieve_offerers_bank_information
from utils.config import API_ROOT_PATH
from utils.logger import logger
from utils.mailing import MAILJET_API_KEY, MAILJET_API_SECRET

app = Flask(__name__, template_folder='../templates')
app.config['SQLALCHEMY_DATABASE_URI'] = os.environ.get('DATABASE_URL')
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
app.config['DEBUG'] = True
db.init_app(app)


def pc_send_final_booking_recaps():
    print("[BATCH] Cron send_final_booking_recaps: START")
    with app.app_context():
        from scripts.send_final_booking_recaps import send_final_booking_recaps
        app.mailjet_client = Client(auth=(MAILJET_API_KEY, MAILJET_API_SECRET), version='v3')
        send_final_booking_recaps()

    print("[BATCH] Cron send_final_booking_recaps: END")


def pc_generate_and_send_payments():
    logger.info("[BATCH][PAYMENTS] Cron generate_and_send_payments: START")

    with app.app_context():
        from scripts.payments import generate_and_send_payments
        app.mailjet_client = Client(auth=(MAILJET_API_KEY, MAILJET_API_SECRET), version='v3')
        generate_and_send_payments()

    logger.info("[BATCH][PAYMENTS] Cron generate_and_send_payments: END")


def pc_retrieve_offerers_bank_information():
    logger.info("[BATCH][BANK INFORMATION] Cron retrieve_offerers_bank_information: START")
    with app.app_context():
        process = subprocess.Popen('PYTHONPATH="." python scripts/pc.py update_providables'
                             + ' --provider BankInformationProvider',
                             shell=True,
                             cwd=API_ROOT_PATH)
        output, error = process.communicate()
        logger.info(StringIO(output))
    logger.info("[BATCH][BANK INFORMATION] Cron retrieve_offerers_bank_information: END")


if __name__ == '__main__':
    scheduler = BlockingScheduler()
    if feature_cron_send_final_booking_recaps_enabled():
        scheduler.add_job(pc_send_final_booking_recaps, 'cron', id='send_final_booking_recaps', day='*')
    if feature_cron_generate_and_send_payments():
        scheduler.add_job(pc_generate_and_send_payments, 'cron', id='generate_and_send_payments', day='1,15')
    if feature_cron_retrieve_offerers_bank_information():
        scheduler.add_job(pc_retrieve_offerers_bank_information, 'cron', id='retrieve_offerers_bank_information',
                          day='*')
    scheduler.start()
