import argparse
import datetime
import decimal
import json
import os
import sys

import requests

import pcapi.core.offers.models as offers_models
from pcapi.flask_app import app
from pcapi.utils.human_ids import humanize


HOST = "https://search-testing.ent.europe-west1.gcp.cloud.es.io"
PRIVATE_API_KEY = os.environ["APP_SEARCH_PRIVATE_API_KEY"]

ENGINE_NAME = "offers"
ENGINE_LANGUAGE = None

SCHEMA = {
    "offer_author": "text",
    "offer_category": "text",
    "offer_date_created": "date",
    "offer_dates": "date",
    "offer_description": "text",
    "offer_is_digital": "number",
    "offer_is_duo": "number",
    "offer_is_event": "number",
    "offer_isbn": "text",
    "offer_label": "text",
    "offer_music_type": "text",
    "offer_name": "text",
    "offer_performer": "text",
    "offer_prices": "number",
    "offer_ranking_weight": "number",
    "offer_show_type": "text",
    "offer_speaker": "text",
    "offer_stage_director": "text",
    "offer_stocks_date_created": "text",
    "offer_tags": "text",
    "offer_times": "text",
    "offer_thumb_url": "text",
    "offer_type": "text",
    "offerer_name": "text",
    "venue_city": "text",
    "venue_department_code": "text",
    "venue_name": "text",
    "venue_position": "geolocation",
    "venue_public_name": "text",
}


# FIXME (dbaty): we're going to try without this default position.
# DEFAULT_LONGITUDE = 2.409289
# DEFAULT_LATITUDE = 47.158459


def _call_api(method, endpoint, data):
    headers = {"Authorization": f"Bearer {PRIVATE_API_KEY}", "Content-Type": "application/json"}
    url = f"{HOST}{endpoint}"
    data = json.dumps(data, cls=AppSearchJsonEncoder)
    response = requests.request(method, url, headers=headers, data=data)
    if not response.ok:
        result = response.json()
        try:
            errors = [result["error"]]
        except KeyError:
            errors = result["errors"]
        print("\n".join(f"ERR: {error}" for error in errors))
        return False
    return True


def create_engine():
    endpoint = "/api/as/v1/engines"
    data = {"name": ENGINE_NAME, "language": ENGINE_LANGUAGE}
    if _call_api("POST", endpoint, data):
        print("Engine has been created.")


def init_schema():
    endpoint = f"/api/as/v1/engines/{ENGINE_NAME}/schema"
    if _call_api("POST", endpoint, SCHEMA):
        print("Schema has been initialized.")


# FIXME : in tests, check that this function does not return any
# boolean. Boolean values would be rejected by App Search API. They
# must be converted as integers. It's not easy to do that at the
# serialization level.
def serialize(offer):
    dates = []
    if offer.isEvent:
        dates = [stock.beginningDatetime.timestamp() for stock in offer.bookableStocks]
    extra_data = offer.extraData
    # FIXME: see Cyril's FIXME about that.
    isbn = (extra_data.get("isbn") or extra_data.get("visa")) if extra_data else None

    venue = offer.venue
    if venue.longitude is not None and venue.latitude is not None:
        position = [venue.longitude, venue.latitude]
    else:
        position = None

    return {
        "id": offer.id,
        "author": extra_data.get("author") if extra_data else None,
        "category": offer.offer_category_name_for_app,
        "date_created": offer.dateCreated,
        "dates": dates,
        "description": offer.description,
        "human_id": humanize(offer.id),
        "is_digital": int(offer.isDigital),
        "is_duo": int(offer.isDuo),
        "is_event": int(offer.isEvent),
        "isbn": isbn,
        "label": offer.offerType["appLabel"],
        "music_type": extra_data.get("musicType") if extra_data else None,
        "name": offer.name,
        "performer": extra_data.get("performer") if extra_data else None,
        "prices": [int(stock.price * 100) for stock in offer.bookableStocks],
        "ranking_weight": offer.rankingWeight,
        "show_type": extra_data.get("showType") if extra_data else None,
        "speaker": extra_data.get("speaker") if extra_data else None,
        "stage_director": extra_data.get("stageDirector") if extra_data else None,
        "thumb_url": offer.thumbUrl,  # FIXME: return last part of the path only
        "offerer_name": venue.managingOfferer.name,
        "venue_city": venue.city,
        "venue_department_code": venue.departementCode,
        "venue_name": venue.name,
        "venue_position": position,
        "venue_public_name": venue.publicName,
    }


class AppSearchJsonEncoder(json.JSONEncoder):
    def default(self, obj):
        if isinstance(obj, datetime.datetime):
            return obj.isoformat().split(".")[0] + "Z"
        if isinstance(obj, decimal.Decimal):
            return float(obj)
        return super().default(obj)


def index_offers():
    endpoint = f"/api/as/v1/engines/{ENGINE_NAME}/documents"
    documents = []
    with app.app_context():
        offers = offers_models.Offer.query.all()
        for offer in offers:
            if offer.isBookable:
                print(f"Found {offer} to add to index")
                documents.append(serialize(offer))
    if documents:
        if _call_api("POST", endpoint, documents):
            print(f"Successfully created or updated {len(documents)} offers")
    else:
        print("ERR: Could not find any bookable offers to index")


def get_parser():
    parser = argparse.ArgumentParser()

    main_subparsers = parser.add_subparsers()

    # engine (create)
    engine = main_subparsers.add_parser("engine", help="Commands related to engines.")
    engine_subparsers = engine.add_subparsers()
    engine_create = engine_subparsers.add_parser("create", help="Create a new engine.")
    engine_create.set_defaults(callback=create_engine)

    # schema (init)
    schema = main_subparsers.add_parser("schema", help="Commands related to the schema.")
    schema_subparsers = schema.add_subparsers()
    schema_create = schema_subparsers.add_parser("init", help="Initialize the schema.")
    schema_create.set_defaults(callback=init_schema)

    # offers (index)
    offers = main_subparsers.add_parser("offers", help="Commands related to offers.")
    offers_subparsers = offers.add_subparsers()
    offers_create = offers_subparsers.add_parser("index", help="Index offers.")
    offers_create.set_defaults(callback=index_offers)

    return parser


def main():
    parser = get_parser()
    args = parser.parse_args()
    if not hasattr(args, "callback"):
        parser.print_usage()
        sys.exit(os.EX_USAGE)

    args = dict(vars(args))
    callback = args.pop("callback")
    callback()


if __name__ == "__main__":
    main()
