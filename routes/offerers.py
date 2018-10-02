""" offerers """
from flask import current_app as app, jsonify, request
from flask_login import current_user, login_required

from domain.admin_emails import maybe_send_offerer_validation_email
from models import Offerer, PcObject, RightsType
from models.venue import create_digital_venue
from repository.booking_queries import find_offerer_bookings
from repository.user_offerer_queries import filter_query_where_user_is_user_offerer_and_is_validated
from utils.human_ids import dehumanize
from utils.includes import OFFERER_INCLUDES
from utils.mailing import MailServiceException
from utils.rest import ensure_current_user_has_rights, \
                       expect_json_data, \
                       handle_rest_get_list, \
                       load_or_404, \
                       login_or_api_key_required
from utils.search import get_keywords_filter


@app.route('/offerers', methods=['GET'])
@login_required
def list_offerers():
    query = Offerer.query

    if not current_user.isAdmin:
        query = filter_query_where_user_is_user_offerer_and_is_validated(query, current_user)

    keywords = request.args.get('keywords')
    if keywords is not None:
        query = query.filter(get_keywords_filter([Offerer], keywords))

    return handle_rest_get_list(Offerer,
                                include=OFFERER_INCLUDES,
                                order_by=Offerer.name,
                                page=request.args.get('page'),
                                paginate=10,
                                query=query)


@app.route('/offerers/<id>', methods=['GET'])
@login_required
def get_offerer(id):
    ensure_current_user_has_rights(RightsType.editor, dehumanize(id))
    offerer = load_or_404(Offerer, id)
    return jsonify(offerer._asdict(include=OFFERER_INCLUDES)), 200

@app.route('/offerers/<id>/bookings', methods=['GET'])
@login_required
def get_offerer_bookings(id):

    offerer_id = dehumanize(id)

    ensure_current_user_has_rights(RightsType.editor, offerer_id)

    return find_offerer_bookings(
        offerer_id,
        search=request.args.get('search'),
        order_by=request.args.get('order_by'),
        page=request.args.get('page', 1)
    )

@app.route('/offerers', methods=['POST'])
@login_or_api_key_required
@expect_json_data
def create_offerer():
    offerer = Offerer()
    offerer.populateFromDict(request.json)

    digital_venue = create_digital_venue(offerer)

    PcObject.check_and_save(offerer, digital_venue)

    if not current_user.isAdmin:
        offerer.generate_validation_token()
        user_offerer = offerer.give_rights(current_user,
                                           RightsType.admin)
        PcObject.check_and_save(offerer, user_offerer)
        try:
            maybe_send_offerer_validation_email(offerer, user_offerer, app.mailjet_client.send.create)
        except MailServiceException as e:
            app.logger.error('Mail service failure', e)
    return jsonify(offerer._asdict(include=OFFERER_INCLUDES)), 201


@app.route('/offerers/<offererId>', methods=['PATCH'])
@login_or_api_key_required
@expect_json_data
def patch_offerer(offererId):
    offerer = Offerer.query.filter_by(id=dehumanize(offererId)).first()
    offerer.populateFromDict(request.json, skipped_keys=['validationToken'])
    PcObject.check_and_save(offerer)
    return jsonify(offerer._asdict(include=OFFERER_INCLUDES)), 200
