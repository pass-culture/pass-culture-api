import argparse
import datetime
import decimal
import json
import os
import sys

import requests

import pcapi.core.offers.models as offers_models
from pcapi.flask_app import app


HOST = "https://search-testing.ent.europe-west1.gcp.cloud.es.io"
PRIVATE_API_KEY = os.environ["APP_SEARCH_PRIVATE_API_KEY"]

ENGINE_NAME = "offers"
ENGINE_LANGUAGE = None

# FIXME: replace "author", "speaker", "performer" and "stage_director"
# fields by a single "searchable_text" field that holds everything in
# a space-separated string.
SCHEMA = {
    "author": "text",
    "category": "text",
    "date_created": "date",
    "dates": "date",
    "description": "text",
    "is_digital": "number",
    "is_duo": "number",
    "is_event": "number",
    "is_thing": "number",
    "isbn": "text",
    "label": "text",
    "music_type": "text",
    "name": "text",
    "performer": "text",
    "prices": "number",
    "ranking_weight": "number",
    "show_type": "text",
    "speaker": "text",
    "stage_director": "text",
    "stocks_date_created": "text",
    "tags": "text",
    "times": "text",
    "thumb_url": "text",
    "type": "text",
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

    serialize = AppSearch().serialize

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
