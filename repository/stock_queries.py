from datetime import datetime

from models import Stock, Offerer, User, PcObject, Offer, ThingType, Venue, Product
from utils.human_ids import dehumanize


def find_stock_by_id(id: int) -> Stock:
    return Stock.query.get(id)


def find_stocks_with_possible_filters(filters, user):
    query = Stock.queryNotSoftDeleted()
    if 'offererId' in filters:
        query = query.filter(Stock.offererId == dehumanize(filters['offererId']))
        _check_offerer_user(query.first_or_404().offerer.query, user)
    if 'hasPrice' in filters and filters['hasPrice'].lower() == 'true':
        query = query.filter(Stock.price != None)
    return query


def set_booking_recap_sent_and_save(stock):
    stock.bookingRecapSent = datetime.utcnow()
    PcObject.save(stock)


def find_stocks_of_finished_events_when_no_recap_sent():
    return Stock.queryNotSoftDeleted() \
        .filter((Stock.bookingLimitDatetime < datetime.utcnow()) &
                (Stock.beginningDatetime < datetime.utcnow()) &
                (Stock.bookingRecapSent == None))


def find_online_activation_stock():
    return Stock.query \
        .join(Offer) \
        .join(Venue) \
        .filter_by(isVirtual=True) \
        .join(Product, Offer.productId == Product.id) \
        .filter_by(type=str(ThingType.ACTIVATION)) \
        .first()


def _check_offerer_user(query, user):
    return query.filter(
        Offerer.users.any(User.id == user.id)
    ).first_or_404()
