from flask import current_app as app
from flask_jwt_extended import get_jwt_identity
from flask_jwt_extended import jwt_required

from pcapi import settings
from pcapi.core.users import api
from pcapi.core.users import exceptions
from pcapi.models import ApiErrors
from pcapi.repository.user_queries import find_user_by_email
from pcapi.serialization.decorator import spectree_serialize
from pcapi.validation.routes.captcha import ReCaptchaException
from pcapi.validation.routes.captcha import check_recaptcha_token_is_valid

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
    user = find_user_by_email(identifier)

    if user is None:
        app.logger.error("Authenticated user with email %s not found", identifier)
        raise ApiErrors({"email": ["Utilisateur introuvable"]})

    return serializers.UserProfileResponse.from_orm(user)


@blueprint.native_v1.route("/account", methods=["POST"])
@spectree_serialize(on_success_status=204, api=blueprint.api, on_error_statuses=[400])
def create_account(body: serializers.AccountRequest) -> None:
    if settings.NATIVE_ACCOUNT_CREATION_REQUIRES_RECAPTCHA:
        try:
            check_recaptcha_token_is_valid(body.token, "submit", settings.RECAPTCHA_RESET_PASSWORD_MINIMAL_SCORE)
        except ReCaptchaException:
            raise ApiErrors({"token": "The given token is not invalid"})
    try:
        api.create_account(
            email=body.email,
            password=body.password,
            birthdate=body.birthdate,
            has_allowed_recommendations=body.has_allowed_recommendations,
            is_email_validated=False,
        )
    except exceptions.UserAlreadyExistsException:
        user = find_user_by_email(body.email)
        api.request_password_reset(user)
    except exceptions.UnderAgeUserException:
        raise ApiErrors({"dateOfBirth": "The birthdate is invalid"})


@blueprint.native_v1.route("/resend_email_validation", methods=["POST"])
@spectree_serialize(on_success_status=204, api=blueprint.api)
def resend_email_validation(body: serializers.ResendEmailValidationRequest) -> None:
    user = find_user_by_email(body.email)
    if not user or not user.isActive:
        return
    try:
        if user.isEmailValidated:
            api.request_password_reset(user)
        else:
            api.request_email_confirmation(user)
    except exceptions.EmailNotSent:
        raise ApiErrors(
            {"code": "EMAIL_NOT_SENT", "general": ["L'email n'a pas pu être envoyé"]},
            status_code=400,
        )


@blueprint.native_v1.route("/id_check_token", methods=["GET"])
@spectree_serialize(api=blueprint.api, response_model=serializers.GetIdCheckTokenResponse)
@jwt_required
def get_id_check_token() -> serializers.GetIdCheckTokenResponse:
    identifier = get_jwt_identity()
    user = find_user_by_email(get_jwt_identity())

    if user is None:
        app.logger.error("Authenticated user with email %s not found", identifier)
        raise ApiErrors({"email": ["Utilisateur introuvable"]})

    id_check_token = api.create_id_check_token(user)

    return serializers.GetIdCheckTokenResponse(token=id_check_token.value if id_check_token else None)
