""" offerers """
from flask import current_app as app, jsonify, request
from flask_login import current_user, login_required

from domain.admin_emails import maybe_send_offerer_validation_email
from domain.reimbursement import find_all_booking_reimbursement
from models import Offerer, PcObject, RightsType
from models.venue import create_digital_venue
from repository.booking_queries import find_offerer_bookings
from repository.user_offerer_queries import filter_query_where_user_is_user_offerer_and_is_validated, find_pending_offerer_by_user
from utils.human_ids import dehumanize
from utils.includes import PRO_BOOKING_INCLUDES, OFFERER_INCLUDES, PENDING_OFFERER_INCLUDES
from utils.mailing import MailServiceException
from utils.rest import ensure_current_user_has_rights, \
    expect_json_data, \
    handle_rest_get_list, \
    load_or_404, \
    login_or_api_key_required
from utils.search import get_keywords_filter
from validation.offerers import check_valid_edition


@app.route('/offerers', methods=['GET'])
@login_required
def list_offerers():
    query = Offerer.query

    if not current_user.isAdmin:
        query = filter_query_where_user_is_user_offerer_and_is_validated(query, current_user)

    keywords = request.args.get('keywords')
    if keywords is not None:
        query = query.filter(get_keywords_filter([Offerer], keywords))

    offerers = handle_rest_get_list(Offerer,
                                include=OFFERER_INCLUDES,
                                order_by=Offerer.name,
                                page=request.args.get('page'),
                                paginate=10,
                                query=query)
    if request.args.get('page') == "1":
        raw_pending_offerers = find_pending_offerer_by_user(current_user)
        pending_offerers = [
            o._asdict(include=PENDING_OFFERER_INCLUDES) for o in raw_pending_offerers
        ]
        offerers = jsonify(pending_offerers + offerers[0].json), 200

    return offerers


@app.route('/offerers/<id>', methods=['GET'])
@login_required
def get_offerer(id):
    ensure_current_user_has_rights(RightsType.editor, dehumanize(id))
    offerer = load_or_404(Offerer, id)
    return jsonify(offerer._asdict(include=OFFERER_INCLUDES)), 200


@app.route('/offerers/<id>/bookings', methods=['GET'])
@login_required
def get_offerer_bookings(id):
    ensure_current_user_has_rights(RightsType.editor, dehumanize(id))
    order_by_key = request.args.get('order_by_column')
    order = request.args.get('order')
    order_by = _generate_orderby_criterium(order, order_by_key)
    bookings = find_offerer_bookings(
        dehumanize(id),
        search=request.args.get('search'),
        order_by=order_by,
        page=request.args.get('page', 1)
    )

    bookings_reimbursements = find_all_booking_reimbursement(bookings)

    return jsonify([b.as_dict(include=PRO_BOOKING_INCLUDES) for b in bookings_reimbursements]), 200


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
    ensure_current_user_has_rights(RightsType.admin, dehumanize(offererId))
    data = request.json
    check_valid_edition(data)
    offerer = Offerer.query.filter_by(id=dehumanize(offererId)).first()
    offerer.populateFromDict(data, skipped_keys=['validationToken'])
    PcObject.check_and_save(offerer)
    return jsonify(offerer._asdict(include=OFFERER_INCLUDES)), 200


def _generate_orderby_criterium(order, order_by_key):
    allowed_columns_for_order = {'booking_id': 'booking.id', 'venue_name': 'venue.name',
                                 'date': 'booking."dateCreated"', 'category': "COALESCE(thing.type, event.type)",
                                 'amount': 'booking.amount'}
    if order_by_key and order:
        column = allowed_columns_for_order[order_by_key]
        order_by = '{} {}'.format(column, order)
    else:
        order_by = None
    return order_by
