from contextlib import contextmanager
import typing

import sentry_sdk
from sentry_sdk import capture_exception
from sentry_sdk.integrations.flask import FlaskIntegration
from sentry_sdk.integrations.redis import RedisIntegration
from sentry_sdk.integrations.rq import RqIntegration
from sentry_sdk.integrations.sqlalchemy import SqlalchemyIntegration

from pcapi import settings
from pcapi.utils.health_checker import read_version_from_file


def init_sentry_sdk():
    if settings.IS_DEV:
        return
    # pylint: disable=abstract-class-instantiated
    sentry_sdk.init(
        dsn=settings.SENTRY_DSN,
        integrations=[FlaskIntegration(), RedisIntegration(), RqIntegration(), SqlalchemyIntegration()],
        release=read_version_from_file(),
        environment=settings.ENV,
        traces_sample_rate=settings.SENTRY_SAMPLE_RATE,
    )


ExceptionType = typing.Type[Exception]
ExceptionIterable = tuple[ExceptionType]


@contextmanager
def suppress_and_capture_errors(exception_classes: typing.Union[ExceptionType, ExceptionIterable]) -> typing.Generator:
    """
    Catch specified errors, send error information to Sentry, and
    ignore them.

    Usage:
        with suppress_and_capture_errors(Exception):
            # ...

        with suppress_and_capture_errors((ValueError, MemoryError)):
            # ...
    """
    try:
        yield
    except exception_classes as exc:
        capture_exception(exc)
