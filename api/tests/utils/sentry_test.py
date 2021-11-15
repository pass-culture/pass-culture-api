import pytest

from pcapi.core.testing import override_settings
from pcapi.utils import sentry


@override_settings(IS_DEV=False)
def test_init_sentry_sdk():
    # There is not much to test here, except that the call does not
    # fail.
    sentry.init_sentry_sdk()


def test_suppress_and_capture_errors():
    with sentry.suppress_and_capture_errors(Exception):
        raise RuntimeError("should be suppressed")

    with sentry.suppress_and_capture_errors((RuntimeError, MemoryError)):
        raise MemoryError("should be suppressed")

    with pytest.raises(ValueError):
        with sentry.suppress_and_capture_errors(RuntimeError):
            raise ValueError("should not be suppressed")
