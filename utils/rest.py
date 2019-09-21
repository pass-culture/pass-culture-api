import re
from functools import wraps
from flask import jsonify, request
from flask_login import current_user
from sqlalchemy import text
from sqlalchemy.exc import ProgrammingError
from sqlalchemy.orm.attributes import InstrumentedAttribute
from sqlalchemy.sql.elements import UnaryExpression
from sqlalchemy.sql.functions import random
from sqlalchemy_api_handler import ApiErrors, dehumanize, humanize

from models import Provider
from models.db import db
from utils.string_processing import dashify


def get_provider_from_api_key():
    if 'apikey' in request.headers:
        return Provider.query \
            .filter_by(apiKey=request.headers['apikey']) \
            .first()


def api_key_required(f):
    @wraps(f)
    def wrapper(*args, **kwds):
        request.provider = get_provider_from_api_key()
        if request.provider is None:
            return "API key required", 403
        return f(*args, **kwds)

    return wrapper


def login_or_api_key_required(f):
    @wraps(f)
    def wrapper(*args, **kwds):
        request.provider = get_provider_from_api_key()
        if request.provider is None:
            if not current_user.is_authenticated:
                return "API key or login required", 403
        return f(*args, **kwds)

    return wrapper


def expect_json_data(f):
    @wraps(f)
    def wrapper(*args, **kwds):
        if request.json is None:
            return "JSON data expected", 400
        return f(*args, **kwds)

    return wrapper


def add_table_if_missing(sql_identifier, modelClass):
    if sql_identifier.find('.') == -1:
        return '"' + dashify(modelClass.__name__) + '".' + sql_identifier
    return sql_identifier


def ensure_provider_can_update(obj):
    if request.provider \
            and obj.lastProvider != request.provider:
        return "API key or login required", 403


def ensure_current_user_has_rights(rights, offerer_id, user=current_user):
    if not user.hasRights(rights, offerer_id):
        errors = ApiErrors()
        errors.add_error(
            'global',
            "Vous n'avez pas les droits d'accès suffisant pour accéder à cette information."
        )
        errors.status_code = 403
        raise errors


def feed(entity, json, keys):
    for key in keys:
        if key in json:
            entity.__setattr__(key, json[key])


def delete(entity):
    db.session.delete(entity)
    db.session.commit()
    return jsonify({"id": humanize(entity.id)}), 200


def load_or_404(obj_class, human_id):
    return obj_class.query.filter_by(id=dehumanize(human_id)) \
        .first_or_404()


def load_or_raise_error(obj_class, human_id):
    data = obj_class.query.filter_by(id=dehumanize(human_id)).first()
    if data is None:
        errors = ApiErrors()
        errors.add_error(
            'global',
            'Aucun objet ne correspond à cet identifiant dans notre base de données'
        )
        errors.status_code = 400
        raise errors
    else:
        return data
