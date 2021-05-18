from pcapi.core.bookings import conf
from pcapi.models.feature import FeatureToggle
from pcapi.models.feature import get_features_dict
from pcapi.serialization.decorator import spectree_serialize

from . import blueprint
from .serialization import settings as serializers


@blueprint.native_v1.route("/settings", methods=["GET"])
@spectree_serialize(api=blueprint.api, response_model=serializers.SettingsResponse)
def get_settings() -> serializers.SettingsResponse:
    feature_dict = get_features_dict(
        [
            FeatureToggle.ENABLE_NATIVE_APP_RECAPTCHA.name,
            FeatureToggle.ALLOW_IDCHECK_REGISTRATION.name,
            FeatureToggle.AUTO_ACTIVATE_DIGITAL_BOOKINGS.name,
            FeatureToggle.ENABLE_NATIVE_ID_CHECK_VERSION.name,
            FeatureToggle.ENABLE_PHONE_VALIDATION.name,
            FeatureToggle.APPLY_BOOKING_LIMITS_V2.name,
        ]
    )

    current_deposit_version = conf.get_current_deposit_version(feature_dict[FeatureToggle.APPLY_BOOKING_LIMITS_V2.name])
    booking_configuration = conf.LIMIT_CONFIGURATIONS[current_deposit_version]

    return serializers.SettingsResponse(
        deposit_amount=booking_configuration.TOTAL_CAP,
        is_recaptcha_enabled=feature_dict[FeatureToggle.ENABLE_NATIVE_APP_RECAPTCHA.name],
        allow_id_check_registration=feature_dict[FeatureToggle.ALLOW_IDCHECK_REGISTRATION.name],
        auto_activate_digital_bookings=feature_dict[FeatureToggle.AUTO_ACTIVATE_DIGITAL_BOOKINGS.name],
        enable_native_id_check_version=feature_dict[FeatureToggle.ENABLE_NATIVE_ID_CHECK_VERSION.name],
        enable_phone_validation=feature_dict[FeatureToggle.ENABLE_PHONE_VALIDATION.name],
    )
