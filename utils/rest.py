""" rest """
import re
from functools import wraps
from flask import jsonify, request
from flask_login import current_user
from sqlalchemy.exc import ProgrammingError

from models.api_errors import ApiErrors
from models.db import db
from models.soft_deletable_mixin import SoftDeletableMixin
from utils.human_ids import dehumanize, humanize
from utils.string_processing import dashify


def get_provider_from_api_key():
    if 'apikey' in request.headers:
        Provider = Provider
        return Provider.query\
                       .filter_by(apiKey=request.headers['apikey'])\
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
        return '"'+dashify(modelClass.__name__)+'".'+sql_identifier
    return sql_identifier

def query_with_order_by(query, order_by):
    if order_by:
        try:
            order_by = [order_by] if not isinstance(order_by, list)\
                       else order_by
            query = query.order_by(*order_by)
        except ProgrammingError as e:
            field = re.search('column "?(.*?)"? does not exist', e._message, re.IGNORECASE)
            if field:
                errors = ApiErrors()
                errors.addError('order_by', 'order_by value references an unknown field : '+field.group(1))
                raise errors
            else:
                raise e
    return query

def handle_rest_get_list(modelClass,
                         query=None,
                         refine=None,
                         order_by=None,
                         flask_request=None,
                         meta_data=None,
                         include=None,
                         resolve=None,
                         print_elements=None,
                         paginate=None,
                         page=None):

    # REQUEST
    if flask_request is None:
        flask_request = request

    # QUERY
    if query is None:
        query = modelClass.query

    # DELETED
    if issubclass(modelClass, SoftDeletableMixin):
        query = query.filter_by(isSoftDeleted=False)

    # REFINE
    if refine:
        query = refine(query)

    # ORDER BY
    if order_by:
        query = query_with_order_by(query, order_by)

    # HEADERS
    headers = {}

    # PAGINATE
    if paginate:
        if page is not None:
            page = int(page)
        query = query.paginate(page, per_page=paginate, error_out=False)\

        print("qdqd", query.pages, query.items, dir(query), "iter_pages", query.iter_pages)
        print('query.total', query.total)

        pagination = {
            "itemsCount": query.total,
            "itemsPerPage": query.per_page,
            "pagesCount": query.pages
        }

        if query.has_next:
            pagination["next"] = query.next
        if query.has_prev:
            pagination["prev"] = query.next

        headers['X-Pagination'] = pagination

        elements = query.items

    else:
        elements = query.all()

    # METADATA
    if meta_data:
        headers['X-Metadata'] = meta_data(elements)

    # DICTIFY
    dict_elements = [
        element._asdict(
            include=include,
            resolve=resolve,
        ) for element in elements
    ]

    # PRINT
    if print_elements:
        print(dict_elements)

    # RETURN
    return jsonify(dict_elements), 200, headers


def ensure_provider_can_update(obj):
    if request.provider\
       and obj.lastProvider != request.provider:
        return "API key or login required", 403


def ensure_current_user_has_rights(rights, offerer_id):
    if not current_user.hasRights(rights, offerer_id):
        errors = ApiErrors()
        errors.addError(
            'global',
            "Cette structure n'est pas enregistrée chez cet utilisateur."
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
    return obj_class.query.filter_by(id=dehumanize(human_id))\
                          .first_or_404()
