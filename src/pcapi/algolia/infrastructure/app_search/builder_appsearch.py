from datetime import datetime
from typing import Dict

from pcapi.models import Offer
from pcapi.utils.date import get_time_in_seconds_from_datetime
from pcapi.utils.human_ids import humanize


DEFAULT_LONGITUDE_FOR_NUMERIC_OFFER = 2.409289
DEFAULT_LATITUDE_FOR_NUMERIC_OFFER = 47.158459


def build_appsearch_object(offer: Offer) -> Dict:
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
        "object_id": offer.id,
        "offer_author": author,
        "offer_category": offer.offer_category,
        "offer_date_created": date_created,
        "offer_dates": sorted(dates),
        "offer_description": offer.description,
        "offer_id": humanize_offer_id,
        "offer_pk": offer.id,
        "offer_isbn": isbn,
        "offer_is_digital": int(offer.isDigital),
        "offer_is_duo": int(offer.isDuo),
        "offer_is_event": int(offer.isEvent),
        "offer_is_thing": int(offer.isThing),
        "offer_label": offer.offerType["appLabel"],
        "offer_music_sub_type": music_sub_type,
        "offer_music_type": music_type,
        "offer_name": offer.name,
        "offer_performer": performer,
        "offer_prices": prices_sorted,
        "offer_price_min": price_min,
        "offer_price_max": price_max,
        "offer_show_sub_type": show_sub_type,
        "offer_show_type": show_type,
        "offer_speaker": speaker,
        "offer_stage_director": stage_director,
        "offer_stocks_date_created": sorted(stocks_date_created),
        "offer_thumb_url": offer.thumbUrl,
        "offer_tags": tags,
        "offer_times": list(set(times)),
        "offer_type": offer.offerType["sublabel"],
        "offer_visa": visa,
        "offer_withdrawal_details": offer.withdrawalDetails,
        "offerer_name": offerer.name,
        "venue_city": venue.city,
        "venue_departement_code": venue.departementCode,
        "venue_name": venue.name,
        "venue_public_name": venue.publicName,
    }

    if has_coordinates:
        object_to_index.update({"geolocation": f"{float(venue.latitude)},{float(venue.longitude)}"})
    else:
        object_to_index.update(
            {"geolocation": f"{DEFAULT_LATITUDE_FOR_NUMERIC_OFFER},{DEFAULT_LONGITUDE_FOR_NUMERIC_OFFER}"}
        )

    return object_to_index
