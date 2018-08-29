""" reset """
from inspect import isclass
from flask import current_app as app, jsonify, request

import models
from models.api_errors import ApiErrors
from models.db import db
from models.pc_object import PcObject

RESET_TOKEN = os.environ.get('RESET_TOKEN')

def check_token():
    if RESET_TOKEN is None or RESET_TOKEN == '':
        raise ValueError("Missing environment variable RESET_TOKEN")
    token = request.args.get('token')
    ae = ApiErrors()
    if token is None:
        ae.addError('token', 'Vous devez préciser un jeton dans l''adresse (token=XXX)')
    if not token == RESET_TOKEN:
        ae.addError('token', 'Le jeton est invalide')
    if ae.errors:
        raise ae

def is_resetable(model_name):
    model = getattr(models, model_name)
    return not model_name == 'PcObject'\
           and isclass(model)\
           and issubclass(model, PcObject)

@app.route('/reset/', methods=['GET'])
def reset():
    check_token()
    return "\n".join([request.host_url+'export/'+model_name
                                      +'?token='+request.args.get('token')
                      for model_name in filter(is_resetable, models.__all__)])

@app.route('/reset/<model_name>', methods=['GET'])
def reset_table(model_name):
    check_token()
    ae = ApiErrors()
    try:
        model = getattr(models, model_name)
    except KeyError:
        ae.addError('global', 'Nom de classe incorrect : '+model_name)
        return jsonify(ae.errors), 400

    if not is_resetable(model_name):
        ae.addError('global', 'Classe non exportable : '+model_name)
        return jsonify(ae.errors), 400

    model.delete()
    deleted_count = db.session.commit()

    return jsonify({ "modelName": model_name, "count": deleted_count })
