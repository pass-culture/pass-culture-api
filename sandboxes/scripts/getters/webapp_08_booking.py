from models import Offer, Stock, EventType, ThingType, Mediation, Product
from models.user import User
from repository.offer_queries import _filter_bookable_stocks_for_discovery
from repository.user_queries import keep_only_webapp_users
from repository.recommendation_queries import find_recommendations_for_user_matching_offers_and_search
from sandboxes.scripts.utils.helpers import get_user_helper, get_offer_helper
from utils.human_ids import humanize


def get_query_join_on_event(query):
  join_on_event = (Offer.id == Stock.offerId)
  query = query.join(Stock, join_on_event)
  return query

def get_query_join_on_thing(query):
  join_on_offer_id = (Offer.id == Stock.offerId)
  query = query.join(Stock, join_on_offer_id)
  return query

def get_non_free_offers_query_by_type(type):
  filter_not_free_price = (Stock.price > 0)
  filter_not_an_activation_offer = \
      (Product.type != str(EventType.ACTIVATION)) \
      | (Product.type != str(ThingType.ACTIVATION))

  query = Offer.query.outerjoin(type)
  query = get_query_join_on_thing(query)
  query = _filter_bookable_stocks_for_discovery(query)
  query = query \
      .filter(filter_not_an_activation_offer) \
      .filter(filter_not_free_price)
  return query

def get_non_free_digital_offer():
  query = get_non_free_offers_query_by_type(Product)
  offer = query \
      .filter(Product.url != None) \
      .first()
  return {
      "offer": get_offer_helper(offer)
  }

def get_non_free_thing_offer_with_active_mediation():
  query = get_non_free_offers_query_by_type(Product)
  offer = query \
      .filter(Product.url == None) \
      .filter(Stock.beginningDatetime == None) \
      .filter(Offer.mediations.any(Mediation.isActive == True)) \
      .first()
  return {
      "mediationId": [humanize(m.id) for m in offer.mediations if m.isActive][0],
      "offer": get_offer_helper(offer)
  }

def get_non_free_event_offer():
  query = get_non_free_offers_query_by_type(Product)
  offer = query.first()
  return {
      "offer": get_offer_helper(offer)
  }

def get_existing_webapp_user_has_no_more_money():
  query = keep_only_webapp_users(User.query)
  query = query.filter(User.email.contains('has-no-more-money'))
  user = query.first()
  return {
      "user": get_user_helper(user)
  }

def get_existing_webapp_user_can_book_thing_offer():
    query = keep_only_webapp_users(User.query)
    query = query.filter(User.email.contains('93.has-confirmed-activation'))
    user = query.first()
    return {
        "user": get_user_helper(user)
    }

def get_existing_webapp_user_can_book_digital_offer():
    query = keep_only_webapp_users(User.query)
    query = query.filter(User.email.contains('93.has-confirmed-activation'))
    user = query.first()
    return {
        "user": get_user_helper(user)
    }

def get_existing_webapp_user_can_book_event_offer():
    query = keep_only_webapp_users(User.query)
    query = query.filter(User.email.contains('93.has-booked-some'))
    user = query.first()
    return {
        "user": get_user_helper(user)
    }

def get_existing_webapp_user_can_book_multidates():
    query = keep_only_webapp_users(User.query)
    query = query.filter(User.email.contains('97.has-confirmed-activation'))
    user = query.first()
    return {
        "user": get_user_helper(user)
    }

def get_existing_webapp_user_reach_digital_limit():
    query = keep_only_webapp_users(User.query)
    query = query.filter(User.email.contains('93.has-booked-some'))
    user = query.first()
    return {
        "user": get_user_helper(user)
    }

def get_existing_webapp_user_reach_physical_limit():
    query = keep_only_webapp_users(User.query)
    query = query.filter(User.email.contains('93.has-booked-some'))
    user = query.first()
    return {
        "user": get_user_helper(user)
    }
