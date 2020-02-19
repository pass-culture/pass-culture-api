import os

from apscheduler.schedulers.blocking import BlockingScheduler
from flask import Flask
from sqlalchemy import orm

from models.db import db
from repository.feature_queries import feature_cron_synchronize_titelive_things, \
    feature_cron_synchronize_titelive_descriptions, \
    feature_cron_synchronize_titelive_thumbs, feature_cron_synchronize_titelive_stocks
from scheduled_tasks.provider import pc_synchronize_titelive_things, pc_synchronize_titelive_descriptions, \
    pc_synchronize_titelive_thumbs
from scheduled_tasks.venue_provider import pc_synchronize_titelive_stocks

app = Flask(__name__, template_folder='../templates')
app.config['SQLALCHEMY_DATABASE_URI'] = os.environ.get('DATABASE_URL')
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
app.config['DEBUG'] = True
db.init_app(app)

if __name__ == '__main__':
    orm.configure_mappers()
    scheduler = BlockingScheduler()

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
                          day='*', hour='6')

    scheduler.start()
