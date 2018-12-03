""" user mediations routes """
import csv
import os
from datetime import datetime
from inspect import isclass
from io import BytesIO, StringIO

from flask import current_app as app, jsonify, request, send_file
from flask_login import current_user, login_required
from postgresql_audit.flask import versioning_manager

import models
from models.api_errors import ApiErrors
from models.pc_object import PcObject
from repository import offerer_queries
from repository.venue_queries import find_filtered_venues
from validation.exports import check_user_is_admin , check_get_venues_params

from utils.includes import OFFERER_INCLUDES_FOR_ADMIN
from utils.rest import expect_json_data



Activity = versioning_manager.activity_cls

EXPORT_TOKEN = os.environ.get('EXPORT_TOKEN')


@app.route('/exports/models', methods=['GET'])
def list_export_urls():
    _check_token()
    return "\n".join([request.host_url + 'exports/models/' + model_name
                      + '?token=' + request.args.get('token')
                      for model_name in filter(_is_exportable, models.__all__)])


@app.route('/exports/models/<model_name>', methods=['GET'])
def export_table(model_name):
    _check_token()
    ae = ApiErrors()
    if model_name not in models.__all__:
        ae.addError('global', 'Classe inconnue : ' + model_name)
        return jsonify(ae.errors), 400

    try:
        model = getattr(models, model_name)
    except KeyError:
        ae.addError('global', 'Nom de classe incorrect : ' + model_name)
        return jsonify(ae.errors), 400

    if not _is_exportable(model_name):
        ae.addError('global', 'Classe non exportable : ' + model_name)
        return jsonify(ae.errors), 400

    objects = model.query.all()

    if len(objects) == 0:
        return "", 200

    csvfile = StringIO()
    header = _clean_dict_for_export(model_name, objects[0]._asdict()).keys()
    if model_name == 'User':
        header = list(filter(lambda h: h != 'id' and h != 'password', header))
    writer = csv.DictWriter(csvfile, header, extrasaction='ignore')
    writer.writeheader()
    for obj in objects:
        dct = _clean_dict_for_export(model_name, obj._asdict())
        writer.writerow(dct)
    csvfile.seek(0)
    mem = BytesIO()
    mem.write(csvfile.getvalue().encode('utf-8'))
    mem.seek(0)
    csvfile.close()
    return send_file(mem,
                     attachment_filename='export.csv',
                     as_attachment=True)


@app.route('/exports/offerers_siren', methods=['GET'])
def get_all_offerers_with_managing_user_information():
    _check_token()

    result = offerer_queries.find_all_offerers_with_managing_user_information()
    file_name = 'export_%s_offerer_siren.csv' % datetime.utcnow().strftime('%y_%m_%d')
    headers = ['Offerer_id', 'Offerer_name', 'Offerer_siren','Offerer_postalCode',
               'Offerer_city','User_firstName', 'User_lastName', 'User_email', 'User_phoneNumber',
               'User.postalCode']
    return _make_csv_response(file_name, headers, result)


@app.route('/exports/offerers_siren_with_venue', methods=['GET'])
def get_all_offerers_with_managing_user_information_and_venue():
    _check_token()

    result = offerer_queries.find_all_offerers_with_managing_user_information_and_venue()
    file_name = 'export_%s_offerers_siren_with_venue.csv' % datetime.utcnow().strftime('%y_%m_%d')
    headers = ['Offerer_id', 'Offerer_name', 'Offerer_siren', 'Offerer_postalCode', 'Offerer_city',
               'Venue_name', 'Venue.bookingEmail', 'Venue_postalCode', 'User_firstName',
               'User_lastName', 'User_email', 'User_phoneNumber', 'User.postalCode']
    return _make_csv_response(file_name, headers, result)


@app.route('/exports/offerers_siren_with_not_virtual_venue', methods=['GET'])
def get_all_offerers_with_managing_user_information_and_not_virtual_venue():
    _check_token()

    result = offerer_queries.find_all_offerers_with_managing_user_information_and_not_virtual_venue()
    file_name = 'export_%s_offerers_siren_with_not_virtual_venue.csv' % datetime.utcnow().strftime('%y_%m_%d')
    headers = ['Offerer_id', 'Offerer_name', 'Offerer_siren', 'Offerer_postalCode', 'Offerer_city',
               'Venue_name', 'Venue.bookingEmail', 'Venue_postalCode', 'User_firstName',
               'User_lastName', 'User_email', 'User_phoneNumber', 'User.postalCode'] 
    return _make_csv_response(file_name, headers, result)


@app.route('/exports/offerers_with_venue', methods=['GET'])
def get_all_offerers_with_venue():
    _check_token()

    result = offerer_queries.find_all_offerers_with_venue()
    file_name = 'export_%s_offerers_with_venue_venue.csv' % datetime.utcnow().strftime('%y_%m_%d')
    headers = ['Offerer_id', 'Offerer_name', 'Venue_id', 'Venue_name', 'Venue_bookingEmail',
               'Venue_postalCode', 'Venue_isVirtual'] 
    return _make_csv_response(file_name, headers, result)


@app.route('/exports/pending_validation', methods=['GET'])
@login_required
def get_pending_validation():
    check_user_is_admin(current_user)
    result = []    
    offerers = offerer_queries.find_all_pending_validation()

    for o in offerers:
        result.append(o._asdict(include=OFFERER_INCLUDES_FOR_ADMIN))

    return jsonify(result), 200


@app.route('/exports/venues', methods=['POST'])
@login_required
@expect_json_data
def get_venues():
    check_user_is_admin(current_user)

    params_keys = ['dpt', 'has_validated_offerer', 'zip_codes', 'from_date', 'to_date', 'has_siret',
    'is_virtual', 'offer_status', 'is_validated',  "has_offerer_with_siren", "has_validated_user_offerer", "has_validated_user"]
    params = {}

    for key in params_keys:
        params[key] = request.json.get(key, None)

    check_get_venues_params(params)
    result = find_filtered_venues(dpt=params['dpt'],
                                  zip_codes=params['zip_codes'],
                                  from_date=params['from_date'],
                                  to_date=params['to_date'],
                                  has_siret=params['has_siret'],
                                  is_virtual=params['is_virtual'],
                                  offer_status=params['offer_status'],
                                  is_validated=params['is_validated'],
                                  has_validated_offerer=params['has_validated_offerer'],
                                  has_offerer_with_siren=params['has_offerer_with_siren'],
                                  has_validated_user_offerer=params['has_validated_user_offerer'],
                                  has_validated_user=params['has_validated_user'])

    return jsonify(result), 200


def _make_csv_response(file_name, headers, result):
    csv_file = StringIO()
    csv_writer = csv.writer(csv_file)
    csv_writer.writerow(headers)
    csv_writer.writerows(result)
    csv_file.seek(0)
    mem = BytesIO()
    mem.write(csv_file.getvalue().encode('utf-8'))
    mem.seek(0)
    csv_file.close()
    return send_file(mem, attachment_filename=file_name, as_attachment=True)


def _check_token():
    if EXPORT_TOKEN is None or EXPORT_TOKEN == '':
        raise ValueError("Missing environment variable EXPORT_TOKEN")
    token = request.args.get('token')
    api_errors = ApiErrors()
    if token is None:
        api_errors.addError('token', 'Vous devez préciser un jeton dans l''adresse (token=XXX)')
    if not token == EXPORT_TOKEN:
        api_errors.addError('token', 'Le jeton est invalide')
    if api_errors.errors:
        raise api_errors


def _is_exportable(model_name):
    model = getattr(models, model_name)
    return not model_name == 'PcObject' \
           and isclass(model) \
           and issubclass(model, PcObject)


def _clean_dict_for_export(model_name, dct):
    if model_name == 'User':
        del (dct['password'])
        del (dct['id'])
    return dct


def valid_time_intervall_or_default(time_intervall):
    if time_intervall == 'year' or time_intervall == 'month' or time_intervall == 'week' or time_intervall == 'day':
        return time_intervall
    return 'day'


def _check_int(checked_int):
    try:
        int(checked_int)
        return checked_int
    except:
        return 0
        