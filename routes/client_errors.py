from pprint import pformat
from flask import current_app as app, request, jsonify
from sqlalchemy_api_handler import logger

from domain.admin_emails import send_dev_email
from utils.mailing import send_raw_email


@app.route('/api/client_errors/store', methods=['POST'])
def post_error():
    if not request.data:
        return jsonify('Data expected'), 400

    data = request.get_json(force=True)

    if not data:
        return jsonify('Data expected'), 400

    send_dev_email(
        'Client JS error',
        '<html><body><pre>%s</pre></body></html>' % pformat(data),
        send_raw_email
    )
    logger.error('[CLIENT ERROR] %s' % data)
    return jsonify('Email correctly sent to dev with client error data'), 200
