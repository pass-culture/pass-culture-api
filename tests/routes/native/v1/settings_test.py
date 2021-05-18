import pytest

from pcapi.core.testing import assert_num_queries
from pcapi.core.testing import override_features

from tests.conftest import TestClient


pytestmark = pytest.mark.usefixtures("db_session")


class SettingsTest:
    @override_features(
        APPLY_BOOKING_LIMITS_V2=False,
        ALLOW_IDCHECK_REGISTRATION=True,
        ENABLE_NATIVE_APP_RECAPTCHA=True,
        AUTO_ACTIVATE_DIGITAL_BOOKINGS=False,
        ENABLE_NATIVE_ID_CHECK_VERSION=False,
        ENABLE_PHONE_VALIDATION=True,
    )
    def test_get_settings_feature_combination_1(self, app):
        with assert_num_queries(1):
            response = TestClient(app.test_client()).get("/native/v1/settings")
        assert response.status_code == 200
        assert response.json == {
            "allowIdCheckRegistration": True,
            "autoActivateDigitalBookings": False,
            "depositAmount": 50000,
            "enableNativeIdCheckVersion": False,
            "isRecaptchaEnabled": True,
            "enablePhoneValidation": True,
        }

    @override_features(
        APPLY_BOOKING_LIMITS_V2=True,
        ALLOW_IDCHECK_REGISTRATION=False,
        ENABLE_NATIVE_APP_RECAPTCHA=False,
        AUTO_ACTIVATE_DIGITAL_BOOKINGS=True,
        ENABLE_NATIVE_ID_CHECK_VERSION=True,
        ENABLE_PHONE_VALIDATION=False,
    )
    def test_get_settings_feature_combination_2(self, app):
        response = TestClient(app.test_client()).get("/native/v1/settings")
        assert response.status_code == 200
        assert response.json == {
            "allowIdCheckRegistration": False,
            "autoActivateDigitalBookings": True,
            "depositAmount": 30000,
            "enableNativeIdCheckVersion": True,
            "isRecaptchaEnabled": False,
            "enablePhoneValidation": False,
        }
