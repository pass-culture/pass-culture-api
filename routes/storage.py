""" storage """
import os.path

from flask import current_app as app, jsonify, request, send_file
from flask_login import login_required

import models
from connectors.thumb_storage import save_thumb
from models import RightsType
from utils.human_ids import dehumanize
from utils.inflect_engine import inflect_engine
from utils.object_storage import local_path
from utils.rest import ensure_current_user_has_rights

print('LOCAL DEV MODE: Using disk based object storage')

GENERIC_STORAGE_MODEL_NAMES = [
    'Mediation',
    'User',
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
    model_name = inflect_engine.singular_noun(collectionName.title(), 1)

    if model_name not in GENERIC_STORAGE_MODEL_NAMES:
        return jsonify({'text': 'upload is not authorized for this model'}), 400

    model = getattr(models, model_name)
    entity = model.query.filter_by(id=dehumanize(id)).first_or_404()

    if model_name == 'Mediation':
        offerer_id = entity.offer.venue.managingOffererId
        ensure_current_user_has_rights(RightsType.editor, offerer_id)

    save_thumb(entity, request.files['file'].read(), int(index))
    return jsonify(entity.as_dict()), 200
