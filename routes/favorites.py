from typing import List
from flask import current_app as app, jsonify, request
from flask_login import current_user, login_required
from sqlalchemy_api_handler import ApiHandler, as_dict, dehumanize, load_or_404

from domain.favorites import create_favorite
from domain.favorites import find_first_matching_booking_from_favorite
from models import Mediation, Offer, Favorite
from models.feature import FeatureToggle
from repository.favorite_queries import find_favorite_for_offer_and_user, \
                                        find_all_favorites_by_user_id
from utils.feature import feature_required
from utils.includes import FAVORITE_INCLUDES, \
    WEBAPP_GET_BOOKING_INCLUDES
from validation.offers import check_offer_id_is_present_in_request


@app.route('/favorites', methods=['POST'])
@feature_required(FeatureToggle.FAVORITE_OFFER)
@login_required
def add_to_favorite():
    mediation = None
    offer_id = request.json.get('offerId')
    mediation_id = request.json.get('mediationId')
    check_offer_id_is_present_in_request(offer_id)

    offer = load_or_404(Offer, offer_id)
    if mediation_id != None:
        mediation = load_or_404(Mediation, mediation_id)

    favorite = create_favorite(mediation, offer, current_user)
    ApiHandler.save(favorite)

    return jsonify(_serialize_favorite(favorite)), 201


@app.route('/favorites/<offer_id>', methods=['DELETE'])
@feature_required(FeatureToggle.FAVORITE_OFFER)
@login_required
def delete_favorite(offer_id):
    dehumanized_offer_id = dehumanize(offer_id)

    favorite = find_favorite_for_offer_and_user(dehumanized_offer_id,
                                                current_user.id) \
        .first_or_404()

    ApiHandler.delete(favorite)

    return jsonify(as_dict(favorite)), 200


@app.route('/favorites', methods=['GET'])
@feature_required(FeatureToggle.FAVORITE_OFFER)
@login_required
def get_favorites():
    favorites = find_all_favorites_by_user_id(current_user.id)

    return jsonify(_serialize_favorites(favorites)), 200


@app.route('/favorites/<favorite_id>', methods=['GET'])
@feature_required(FeatureToggle.FAVORITE_OFFER)
@login_required
def get_favorite(favorite_id):
    favorite = load_or_404(Favorite, favorite_id)
    return jsonify(_serialize_favorite(favorite)), 200


def _serialize_favorites(favorites: List[Favorite]) -> List:
    return list(map(_serialize_favorite, favorites))


def _serialize_favorite(favorite: Favorite) -> dict:
    dict_favorite = as_dict(favorite, includes=FAVORITE_INCLUDES)

    booking = find_first_matching_booking_from_favorite(favorite, current_user)
    if booking:
        dict_favorite['firstMatchingBooking'] = as_dict(
            booking, includes=WEBAPP_GET_BOOKING_INCLUDES)

    return dict_favorite
