from flask import current_app as app
from flask_jwt_extended import get_jwt_identity
from flask_jwt_extended import jwt_required

from pcapi import settings
from pcapi.core.users import api
from pcapi.core.users.models import VOID_FIRST_NAME
from pcapi.models import ApiErrors
from pcapi.models.user_sql_entity import UserSQLEntity
from pcapi.serialization.decorator import spectree_serialize
from pcapi.validation.routes.passwords import check_recaptcha_token_is_valid

from . import blueprint
from .serialization import account as serializers


@blueprint.native_v1.route("/me", methods=["GET"])
@spectree_serialize(
    response_model=serializers.UserProfileResponse,
    on_success_status=200,
    api=blueprint.api,
)  # type: ignore
@jwt_required
def get_user_profile() -> serializers.UserProfileResponse:
    identifier = get_jwt_identity()
    user = UserSQLEntity.query.filter_by(email=identifier).first()

    if user is None:
        app.logger.error("Authenticated user with email %s not found", identifier)
        raise ApiErrors({"email": ["Utilisateur introuvable"]})

    return serializers.UserProfileResponse(
        first_name=user.firstName if user.firstName != VOID_FIRST_NAME else None,
        email=user.email,
        is_beneficiary=user.isBeneficiary,
    )


@blueprint.native_v1.route("/account", methods=["POST"])
@spectree_serialize(on_success_status=204, api=blueprint.api, on_error_statuses=[400])
def create_account(body: serializers.AccountRequest) -> None:
    if settings.NATIVE_ACCOUNT_CREATION_REQUIRES_RECAPTCHA:
        check_recaptcha_token_is_valid(body.token, "submit", settings.RECAPTCHA_RESET_PASSWORD_MINIMAL_SCORE)

    api.create_account(
        email=body.email,
        password=body.password,
        brithdate=body.birthdate,
        has_allowed_recommendations=body.hasAllowedRecommendations,
        is_email_validated=False,
    )
