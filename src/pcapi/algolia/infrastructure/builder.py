from datetime import datetime
from typing import Dict

from pcapi.models import Offer
from pcapi.utils.date import get_time_in_seconds_from_datetime
from pcapi.utils.human_ids import humanize


DEFAULT_LONGITUDE_FOR_NUMERIC_OFFER = 2.409289
DEFAULT_LATITUDE_FOR_NUMERIC_OFFER = 47.158459


def build_object(offer: Offer) -> Dict:
    venue = offer.venue
    offerer = venue.managingOfferer
    humanize_offer_id = humanize(offer.id)
    has_coordinates = venue.latitude is not None and venue.longitude is not None
    author = offer.extraData and offer.extraData.get("author")
    stage_director = offer.extraData and offer.extraData.get("stageDirector")
    visa = offer.extraData and offer.extraData.get("visa")
    isbn = offer.extraData and offer.extraData.get("isbn")
    speaker = offer.extraData and offer.extraData.get("speaker")
    performer = offer.extraData and offer.extraData.get("performer")
    show_type = offer.extraData and offer.extraData.get("showType")
    show_sub_type = offer.extraData and offer.extraData.get("showSubType")
    music_type = offer.extraData and offer.extraData.get("musicType")
    music_sub_type = offer.extraData and offer.extraData.get("musicSubType")
    prices = map(lambda stock: stock.price, offer.bookableStocks)
    prices_sorted = sorted(prices, key=float)
    price_min = prices_sorted[0]
    price_max = prices_sorted[-1]
    dates = []
    times = []
    if offer.isEvent:
        dates = [datetime.timestamp(stock.beginningDatetime) for stock in offer.bookableStocks]
        times = [get_time_in_seconds_from_datetime(stock.beginningDatetime) for stock in offer.bookableStocks]
    date_created = datetime.timestamp(offer.dateCreated)
    stocks_date_created = [datetime.timestamp(stock.dateCreated) for stock in offer.bookableStocks]
    tags = [criterion.name for criterion in offer.criteria]

    object_to_index = {
        "objectID": offer.id,
        "offer": {
            "author": author,
            "category": offer.offer_category,
            "dateCreated": date_created,
            "dates": sorted(dates),
            "description": offer.description,
            "id": humanize_offer_id,
            "pk": offer.id,
            "isbn": isbn,
            "isDigital": offer.isDigital,
            "isDuo": offer.isDuo,
            "isEvent": offer.isEvent,
            "isThing": offer.isThing,
            "label": offer.offerType["appLabel"],
            "musicSubType": music_sub_type,
            "musicType": music_type,
            "name": offer.name,
            "performer": performer,
            "prices": prices_sorted,
            "priceMin": price_min,
            "priceMax": price_max,
            "showSubType": show_sub_type,
            "showType": show_type,
            "speaker": speaker,
            "stageDirector": stage_director,
            "stocksDateCreated": sorted(stocks_date_created),
            "thumbUrl": offer.thumbUrl,
            "tags": tags,
            "times": list(set(times)),
            "type": offer.offerType["sublabel"],
            "visa": visa,
            "withdrawalDetails": offer.withdrawalDetails,
        },
        "offerer": {
            "name": offerer.name,
        },
        "venue": {
            "city": venue.city,
            "departementCode": venue.departementCode,
            "name": venue.name,
            "publicName": venue.publicName,
        },
    }

    if has_coordinates:
        object_to_index.update({"_geoloc": {"lat": float(venue.latitude), "lng": float(venue.longitude)}})
    else:
        object_to_index.update(
            {"_geoloc": {"lat": DEFAULT_LATITUDE_FOR_NUMERIC_OFFER, "lng": DEFAULT_LONGITUDE_FOR_NUMERIC_OFFER}}
        )

    return object_to_index
