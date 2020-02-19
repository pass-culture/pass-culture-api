import os

from apscheduler.schedulers.blocking import BlockingScheduler
from flask import Flask
from sqlalchemy import orm

from models.db import db
from scheduled_tasks.provider import synchronize_titelive_things, synchronize_titelive_descriptions, \
    synchronize_titelive_thumbs
from scheduled_tasks.venue_provider import synchronize_titelive_stocks

app = Flask(__name__, template_folder='../templates')
app.config['SQLALCHEMY_DATABASE_URI'] = os.environ.get('DATABASE_URL')
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
app.config['DEBUG'] = True
db.init_app(app)

if __name__ == '__main__':
    orm.configure_mappers()
    scheduler = BlockingScheduler()

    scheduler.add_job(synchronize_titelive_things, 'cron',
                      [app],
                      id='synchronize_titelive_things',
                      day='*', hour='1')

    scheduler.add_job(synchronize_titelive_descriptions, 'cron',
                      [app],
                      id='synchronize_titelive_descriptions',
                      day='*', hour='2')

    scheduler.add_job(synchronize_titelive_thumbs, 'cron',
                      [app],
                      id='synchronize_titelive_thumbs',
                      day='*', hour='3')

    scheduler.add_job(synchronize_titelive_stocks, 'cron',
                      [app],
                      id='synchronize_titelive_stocks',
                      day='*', hour='6')

    scheduler.start()
