from pcapi.core.testing import override_features

from tests.conftest import TestClient


class SettingsTest:
    @override_features()
    def test_get_default_settings(self, app):
        response = TestClient(app.test_client()).get("/native/v1/settings")

        assert response.status_code == 200
        assert response.json == {"depositAmount": 50000, "isApiAvailable": True}

    @override_features(APPLY_BOOKING_LIMITS_V2=False)
    def test_get_settings_before_generalization(self, app):
        response = TestClient(app.test_client()).get("/native/v1/settings")

        assert response.status_code == 200
        assert response.json["depositAmount"] == 50000

    @override_features(APPLY_BOOKING_LIMITS_V2=True)
    def test_get_settings_after_generalization(self, app):
        response = TestClient(app.test_client()).get("/native/v1/settings")

        assert response.status_code == 200
        assert response.json["depositAmount"] == 30000

    @override_features(ENABLE_CLIENT_APPS=False)
    def test_get_settings_app_up(self, app):
        response = TestClient(app.test_client()).get("/native/v1/settings")

        assert response.status_code == 200
        assert not response.json["isApiAvailable"]

    @override_features(ENABLE_CLIENT_APPS=True)
    def test_get_settings_app_down(self, app):
        response = TestClient(app.test_client()).get("/native/v1/settings")

        assert response.status_code == 200
        assert response.json["isApiAvailable"]
