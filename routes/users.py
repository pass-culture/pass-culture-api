from flask import current_app as app, jsonify, request
from flask_login import current_user, login_required, logout_user, login_user

from repository.user_queries import find_user_by_reset_password_token, find_user_by_email
from use_cases.update_user_informations import update_user_informations, AlterableUserInformations
from routes.serialization import as_dict
from utils.credentials import get_user_with_credentials
from utils.includes import USER_INCLUDES
from utils.login_manager import stamp_session, discard_session
from utils.rest import expect_json_data, \
    login_or_api_key_required
from validation.routes.users import check_allowed_changes_for_user, check_valid_signin


@app.route("/users/current", methods=["GET"])
@login_required
def get_profile():
    user = find_user_by_email(current_user.email)
    return jsonify(as_dict(user, includes=USER_INCLUDES)), 200


@app.route("/users/token/<token>", methods=["GET"])
def check_activation_token_exists(token):
    user = find_user_by_reset_password_token(token)

    if user is None:
        return jsonify(), 404

    return jsonify(), 200


import marshmallow
from marshmallow import fields


# Note : Il y a une recette assez simple pour gérer automatiquement la
# conversion CamelCase vs. snake_case, si besoin :
# https://marshmallow.readthedocs.io/en/latest/examples.html#inflection-camel-casing-keys
# Attention à la génération OpenAPI, par contre.


def validate_department_code(code):
    if code in ('2A', '2B'):
        return
    try:
        int(code)
    except ValueError:
        raise marshmallow.ValidationError("Département incorrect")
    # [...]


class UserUpdateSchema(marshmallow.Schema):
    public_name = fields.String()
    email = fields.Email()
    phone_number = fields.String()
    department_code = fields.String(validate=validate_department_code)
    postal_code = fields.String()
    has_seen_tutorials = fields.Boolean()
    cultural_survey_id = fields.Integer()
    cultural_survey_filled_date = fields.DateTime()
    needs_to_fill_cultural_survey = fields.Boolean()

    @marshmallow.validates_schema
    def validate_postal_and_department_codes_match(self, data, **kwargs):
        # simpliste, évidemment, c'est juste pour donner un exemple
        postal_code = data['postal_code']
        department_code = data['department_code']
        if not postal_code.startswith(department_code):
            raise marshmallow.ValidationError("Le code postal et le département ne correspondent pas.")


class UserSerializer(marshmallow.Schema):
    id  = fields.Integer()
    email = fields.Email()
    phone_number = fields.Email()
    # [...]
    has_physical_venues = fields.Boolean()
    has_offers = fields.Boolean()



@app.route('/users/current', methods=['PATCH'])
@login_or_api_key_required
@expect_json_data
def patch_profile():
    request_data = request.json.keys()

    schema = UserUpdateSchema()
    # load() peut lever une ValidationError, cf. deserialization_error
    # pour le renvoi d'une erreur HTTP 400 automatique.
    schema.load(request_data)

    # je n'aime pas trop cette façon de passer un objet à une fonction
    # de mise à jour, mais c'est un autre sujet.
    user = update_user_informations(schema)

    # On pourrait utiliser `dumps()` (avec un "s") qui renvoie
    # directement du JSON. À voir si `jsonify()` a un intérêt
    # particulier.
    serialized = UserSerializer().dump(user)
    return jsonify(serialized), 200


@app.route("/users/signin", methods=["POST"])
def signin():
    json = request.get_json()
    identifier = json.get("identifier")
    password = json.get("password")
    check_valid_signin(identifier, password)
    user = get_user_with_credentials(identifier, password)
    login_user(user, remember=True)
    stamp_session(user)
    return jsonify(as_dict(user, includes=USER_INCLUDES)), 200


@app.route("/users/signout", methods=["GET"])
@login_required
def signout():
    discard_session()
    logout_user()
    return jsonify({"global": "Deconnecté"})
