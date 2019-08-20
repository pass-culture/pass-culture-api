from models import Mediation, Offer, Stock, User, Product
from models.recommendation import Recommendation
from repository.user_queries import keep_only_webapp_users
from sandboxes.scripts.utils.helpers import get_mediation_helper, \
                                            get_offer_helper, \
                                            get_user_helper, \
                                            get_recommendation_helper
from sandboxes.scripts.utils.bookings import find_offer_compatible_with_bookings, \
                                             get_cancellable_bookings_for_user


def get_existing_webapp_user_with_at_least_one_recommendation():
   query = Recommendation.query.join(User)
   query = keep_only_webapp_users(query)
   query = query.reset_joinpoint().join(Offer)

   recommendation = query.first()
   return {
       "user": get_user_helper(recommendation.user),
       "recommendation": get_recommendation_helper(recommendation)
   }


def get_existing_webapp_hnmm_user(return_as_dict=False):
    query = keep_only_webapp_users(User.query)
    query = query.filter(User.email.contains('93.has-no-more-money'))
    user = query.first()
    if return_as_dict == False:
        return user
    return {
        "user": get_user_helper(user)
    }


def get_existing_webapp_hbs_user():
    query = keep_only_webapp_users(User.query)
    query = query.filter(User.email.contains('has-booked-some'))
    user = query.first()
    return {
        "user": get_user_helper(user)
    }


def get_existing_event_offer_with_active_mediation_already_booked_but_cancellable_and_user_hnmm_93():
    offer_with_stock_id_tuples = Offer.query \
        .filter(Offer.mediations.any(Mediation.isActive)) \
        .join(Stock) \
        .filter(Stock.beginningDatetime != None) \
        .add_columns(Stock.id) \
        .all()
    user = get_existing_webapp_hnmm_user()
    bookings = get_cancellable_bookings_for_user(user)
    offer = find_offer_compatible_with_bookings(offer_with_stock_id_tuples, bookings)

    for mediation in offer.mediations:
        if mediation.isActive:
            return {
                "mediation": get_mediation_helper(mediation),
                "offer": get_offer_helper(offer),
                "user": get_user_helper(user)
            }


def get_existing_digital_offer_with_active_mediation_already_booked_and_user_hnmm_93():
    offer_with_stock_id_tuples = Offer.query.outerjoin(Product) \
        .filter(Offer.mediations.any(Mediation.isActive)) \
        .filter(Product.url != None) \
        .join(Stock, (Offer.id == Stock.offerId)) \
        .add_columns(Stock.id) \
        .all()
    user = get_existing_webapp_hnmm_user()
    bookings = get_cancellable_bookings_for_user(user)
    offer = find_offer_compatible_with_bookings(offer_with_stock_id_tuples, bookings)

    for mediation in offer.mediations:
        if mediation.isActive:
            return {
                "mediation": get_mediation_helper(mediation),
                "offer": get_offer_helper(offer),
                "user": get_user_helper(user)
            }
