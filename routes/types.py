from flask import current_app as app, jsonify
from flask_login import current_user, login_required

from domain.types import get_formatted_active_product_types


@app.route('/types', methods=['GET'])
@login_required
def list_types():
    return jsonify(get_formatted_active_product_types()), 200
