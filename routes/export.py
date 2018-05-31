""" user mediations routes """
import csv
from inspect import isclass
from io import BytesIO, StringIO
from flask import current_app as app, jsonify, request, send_file
import os

from models.api_errors import ApiErrors

EXPORT_TOKEN = os.environ.get('EXPORT_TOKEN')


def check_token():
    if EXPORT_TOKEN is None or EXPORT_TOKEN == '':
        raise ValueError("Missing environment variable EXPORT_TOKEN")
    token = request.args.get('token')
    ae = ApiErrors()
    if token is None:
        ae.addError('token', 'Vous devez préciser un jeton dans l''adresse (token=XXX)')
    if not token == EXPORT_TOKEN:
        ae.addError('token', 'Le jeton est invalide')
    if ae.errors:
        raise ae


def is_exportable(model_name):
    return not model_name == 'PcObject'\
           and isclass(app.model[model_name])\
           and issubclass(app.model[model_name], app.model.PcObject)
           

@app.route('/export/', methods=['GET'])
def list_export_urls():
    check_token()
    return "\n".join([request.host_url+'export/'+model_name
                                      +'?token='+request.args.get('token')
                      for model_name in filter(is_exportable,
                                               app.model.keys())])


@app.route('/export/<model_name>', methods=['GET'])
def export_table(model_name):
    check_token()
    ae = ApiErrors()
    try:
        model = app.model[model_name]
    except KeyError:
        ae.addError('global', 'Nom de classe incorrect : '+model_name)
        return jsonify(ae.errors), 400

    if not is_exportable(model_name):
        ae.addError('global', 'Classe non exportable : '+model_name)
        return jsonify(ae.errors), 400

    objects = model.query.all()
    csvfile = StringIO()
    header = objects[0]._asdict().keys()
    if model_name == 'User':
        header = list(filter(lambda h: h!='id' and h!='password', header))
    writer = csv.DictWriter(csvfile, header)
    writer.writeheader()
    for obj in objects:
        dct = obj._asdict()
        if model_name == 'User':
            del(dct['password'])
            del(dct['id'])
        writer.writerow(dct)
    csvfile.seek(0)
    mem = BytesIO()
    mem.write(csvfile.getvalue().encode('utf-8'))
    mem.seek(0)
    csvfile.close()
    return send_file(mem,
                     attachment_filename='export.csv',
                     as_attachment=True)
