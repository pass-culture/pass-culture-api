import os

from functools import wraps
from models.db import db
from flask import Flask
from sqlalchemy import orm
from functools import wraps
from utils.logger import logger
from workers.logger import build_job_log_message, JobStatus
from flask_app import app


def job_context(func):
    @wraps(func)
    def wrapper(*args, **kwargs):
        with app.app_context():
            return func(*args, **kwargs)
    return wrapper


def log_job(func):
    @wraps(func)
    def wrapper(*args, **kwargs):
        job_description = f"{func.__name__} {args}"
        logger.info(build_job_log_message(job=job_description, status=JobStatus.STARTED))
        result = func(*args, **kwargs)

        logger.info(build_job_log_message(job=job_description, status=JobStatus.ENDED))
        return result

    return wrapper
