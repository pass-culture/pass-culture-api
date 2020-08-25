from typing import List, Dict

from sqlalchemy.orm import selectinload

from models import Recommendation, BookingSQLEntity
from repository import booking_queries
from routes.serialization import as_dict
from utils.human_ids import dehumanize
from utils.includes import RECOMMENDATION_INCLUDES


def serialize_recommendations(recommendations: List[Recommendation], user_id: int) -> dict:
    bookings = BookingSQLEntity.query \
        .distinct(BookingSQLEntity.stockId) \
        .filter(BookingSQLEntity.userId == user_id) \
        .order_by(BookingSQLEntity.stockId, BookingSQLEntity.isCancelled, BookingSQLEntity.dateCreated.desc()) \
        .options(
            selectinload(BookingSQLEntity.stock)
        ) \
        .all()
    bookings_by_offer = _get_bookings_by_offer(bookings)

    print("QUERY BOOKING DONE")

    serialized_recommendations = [serialize_recommendation(recommendation, user_id, query_booking=False)
                                  for recommendation in recommendations]

    print("serialized_recommendations done")
    for serialized_recommendation in serialized_recommendations:
        offer_id = dehumanize(serialized_recommendation["offerId"])
        if offer_id in bookings_by_offer:
            bookings_for_recommendation = bookings_by_offer[offer_id]
        else:
            bookings_for_recommendation = []
        serialized_recommendation['bookings'] = _serialize_bookings(bookings_for_recommendation)
    print("AFTER booking serialize")
    return serialized_recommendations


def serialize_recommendation(recommendation: Recommendation, user_id: int, query_booking: bool = True) -> Dict:
    serialized_recommendation = as_dict(recommendation, includes=RECOMMENDATION_INCLUDES)
    if query_booking and recommendation.offer:
        bookings = booking_queries.find_from_recommendation(recommendation, user_id)
        serialized_recommendation['bookings'] = _serialize_bookings(bookings)

    serialized_recommendation['offer']['isBookable'] = True
    for index, stock in enumerate(serialized_recommendation['offer']['stocks']):
        serialized_recommendation['offer']['stocks'][index]['isBookable'] = True
        serialized_recommendation['offer']['stocks'][index]['remainingQuantity'] = 'unlimited'

    return serialized_recommendation


def _serialize_bookings(bookings: List[BookingSQLEntity]) -> List[Dict]:
    return list(map(_serialize_booking, bookings))


def _serialize_booking(booking: BookingSQLEntity) -> Dict:
    return as_dict(booking)


def _get_bookings_by_offer(bookings: List[BookingSQLEntity]) -> List[BookingSQLEntity]:
    bookings_by_offer = {}

    for booking in bookings:
        offer_id = booking.stock.offerId
        if offer_id in bookings_by_offer:
            bookings_by_offer[offer_id].append(booking)
        else:
            bookings_by_offer[offer_id] = [booking]

    return bookings_by_offer
