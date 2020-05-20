from flask import current_app as app
from flask import jsonify
from flask_login import login_required

from infrastructure.container import get_venue_labels
from routes.serialization.venue_labels_serialize import serialize_venue_label


@app.route('/venue-labels', methods=['GET'])
@login_required
def fetch_venue_labels():
    venue_labels = get_venue_labels.execute()
    return jsonify([serialize_venue_label(venue_label) for venue_label in venue_labels]), 200
