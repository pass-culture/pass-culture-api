from datetime import datetime

from sqlalchemy import func

from models import Recommendation, Mediation, Offer, Stock, EventOccurrence
from utils.config import BLOB_SIZE


def find_unseen_tutorials_for_user(seen_recommendation_ids, user):
    return Recommendation.query.join(Mediation) \
        .filter(
        (Mediation.tutoIndex != None)
        & (Recommendation.user == user)
        & ~Recommendation.id.in_(seen_recommendation_ids)
    ) \
        .order_by(Mediation.tutoIndex) \
        .all()


def count_read_recommendations_for_user(user):
    return filter_out_recommendation_on_soft_deleted_stocks() \
        .filter((Recommendation.user == user) & (Recommendation.dateRead != None)) \
        .count()


def find_all_unread_recommendations(user, seen_recommendation_ids, limit=BLOB_SIZE):
    return filter_out_recommendation_on_soft_deleted_stocks() \
        .outerjoin(Mediation) \
        .filter((Recommendation.user == user)
                & ~Recommendation.id.in_(seen_recommendation_ids)
                & (Mediation.tutoIndex == None)
                & ((Recommendation.validUntilDate == None) | (Recommendation.validUntilDate > datetime.utcnow()))) \
        .filter(Recommendation.dateRead == None) \
        .order_by(func.random()) \
        .limit(limit) \
        .all()


def find_all_read_recommendations(user, seen_recommendation_ids, limit=BLOB_SIZE):
    return filter_out_recommendation_on_soft_deleted_stocks()\
        .outerjoin(Mediation) \
        .filter((Recommendation.user == user)
                & ~Recommendation.id.in_(seen_recommendation_ids)
                & (Mediation.tutoIndex == None)
                & ((Recommendation.validUntilDate == None)
                   | (Recommendation.validUntilDate > datetime.utcnow()))) \
        .filter(Recommendation.dateRead != None) \
        .order_by(func.random()) \
        .limit(limit) \
        .all()

def find_all_recommendations_where_at_least_one_stock_not_soft_deleted():
    all_thing_recommendations_not_soft_deleted = Recommendation.query \
        .join(Offer) \
        .join(Stock) \
        .filter_by(isSoftDeleted=False)
    all_event_recommendations_not_soft_deleted = Recommendation.query \
        .join(Offer) \
        .join(EventOccurrence) \
        .join(Stock) \
        .filter_by(isSoftDeleted=False) \
        .all()
    return all_thing_recommendations_not_soft_deleted + all_event_recommendations_not_soft_deleted


def filter_out_recommendation_on_soft_deleted_stocks():
    join_on_stocks = Recommendation.query \
        .join(Offer) \
        .join(Stock) \
        .filter_by(isSoftDeleted=False)
    join_on_event_occurrences = Recommendation.query \
        .join(Offer) \
        .join(EventOccurrence) \
        .join(Stock) \
        .filter_by(isSoftDeleted=False)

    return join_on_stocks.union_all(join_on_event_occurrences)