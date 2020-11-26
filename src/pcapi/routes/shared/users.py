from flask import jsonify
from flask import request
from flask_login import current_user
from flask_login import login_required
from flask_login import login_user
from flask_login import logout_user

from pcapi.core.users import exceptions as user_exceptions
from pcapi.core.users import repository as user_repo
from pcapi.flask_app import private_api
from pcapi.models.api_errors import ApiErrors
from pcapi.repository.user_queries import find_user_by_email
from pcapi.repository.user_queries import find_user_by_reset_password_token
from pcapi.routes.serialization import as_dict
from pcapi.routes.serialization.users import PatchUserBodyModel
from pcapi.routes.serialization.users import PatchUserResponseModel
from pcapi.serialization.decorator import spectree_serialize
from pcapi.use_cases.update_user_informations import AlterableUserInformations
from pcapi.use_cases.update_user_informations import update_user_informations
from pcapi.utils.includes import USER_INCLUDES
from pcapi.utils.login_manager import discard_session
from pcapi.utils.login_manager import stamp_session
from pcapi.utils.rest import expect_json_data
from pcapi.utils.rest import login_or_api_key_required
from pcapi.validation.routes.users import check_valid_signin


@private_api.route("/users/current", methods=["GET"])
@login_required
def get_profile():
    user = find_user_by_email(current_user.email)
    return jsonify(as_dict(user, includes=USER_INCLUDES)), 200


@private_api.route("/users/token/<token>", methods=["GET"])
def check_activation_token_exists(token):
    user = find_user_by_reset_password_token(token)

    if user is None:
        return jsonify(), 404

    return jsonify(), 200


@private_api.route("/users/current", methods=["PATCH"])
@login_or_api_key_required
@expect_json_data
@spectree_serialize(response_model=PatchUserResponseModel)  # type: ignore
def patch_profile(body: PatchUserBodyModel) -> PatchUserResponseModel:
    user_informations = AlterableUserInformations(id=current_user.id, **body.dict())
    user = update_user_informations(user_informations)
    response_user_model = PatchUserResponseModel.from_orm(user)

    return response_user_model


@private_api.route("/users/signin", methods=["POST"])
def signin():
    json = request.get_json()
    identifier = json.get("identifier")
    password = json.get("password")
    check_valid_signin(identifier, password)
    errors = ApiErrors()
    errors.status_code = 401
    try:
        user = user_repo.get_user_with_credentials(identifier, password)
    except user_exceptions.InvalidIdentifier as exc:
        errors.add_error("identifier", "Identifiant incorrect")
        raise errors from exc
    except user_exceptions.UnvalidatedAccount as exc:
        errors.add_error("identifier", "Ce compte n'est pas validé.")
        raise errors from exc
    except user_exceptions.InvalidPassword as exc:
        errors.add_error("password", "Mot de passe incorrect")
        raise errors from exc
    login_user(user, remember=True)
    stamp_session(user)
    return jsonify(as_dict(user, includes=USER_INCLUDES)), 200


@private_api.route("/users/signout", methods=["GET"])
@login_required
def signout():
    discard_session()
    logout_user()
    return jsonify({"global": "Déconnecté"})
