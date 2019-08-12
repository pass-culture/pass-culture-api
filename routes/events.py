"""events"""
from flask import current_app as app, jsonify

from models import Product
from routes.serialization import as_dict
from utils.includes import EVENT_INCLUDES
from utils.rest import load_or_404, \
    login_or_api_key_required


# FIXME Cette route est-elle utilisée ?
@app.route('/events/<id>', methods=['GET'])
@login_or_api_key_required
def get_event(id):
    event_product = load_or_404(Product, id)
    return jsonify(as_dict(event_product, include=EVENT_INCLUDES)), 200
