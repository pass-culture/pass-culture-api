import os.path
from flask import current_app as app, jsonify, request, send_file
from flask_login import login_required
from sqlalchemy_api_handler import as_dict, dehumanize

from connectors.thumb_storage import save_thumb
from models.db import get_model_with_table_name
from models.user_offerer import RightsType
from utils.inflect_engine import inflect_engine
from utils.object_storage import local_path
from utils.rest import ensure_current_user_has_rights

print('LOCAL DEV MODE: Using disk based object storage')

GENERIC_STORAGE_TABLE_NAMES = [
    'mediation',
    'user',
]


@app.route('/storage/<bucketId>/<path:objectId>')
def send_storage_file(bucketId, objectId):
    path = local_path(bucketId, objectId)
    type_path = str(path) + ".type"
    if os.path.isfile(type_path):
        mimetype = open(type_path).read()
    else:
        return "file not found", 404
    return send_file(open(path, "rb"), mimetype=mimetype)


@app.route('/storage/thumb/<collectionName>/<id>/<index>', methods=['POST'])
@login_required
def post_storage_file(collectionName, id, index):
    table_name = inflect_engine.singular_noun(collectionName, 1)

    if table_name not in GENERIC_STORAGE_TABLE_NAMES:
        return jsonify({'text': 'upload is not authorized for this model'}), 400

    model = get_model_with_table_name(table_name)
    entity = model.query.filter_by(id=dehumanize(id)).first_or_404()

    if table_name == 'mediation':
        offerer_id = entity.offer.venue.managingOffererId
        ensure_current_user_has_rights(RightsType.editor, offerer_id)

    save_thumb(entity, request.files['file'].read(), int(index))
    return jsonify(as_dict(entity)), 200
