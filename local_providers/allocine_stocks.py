import os
import re
from datetime import datetime, timedelta
from typing import List, Optional, Dict, Union

from dateutil import tz
from dateutil.parser import parse
from sqlalchemy import Sequence

from domain.allocine import get_movies_showtimes, get_movie_poster
from local_providers.local_provider import LocalProvider
from local_providers.price_rule import AllocineStocksPriceRule
from local_providers.providable_info import ProvidableInfo
from models import VenueProvider, Offer, Product, EventType, Stock, Venue
from models.db import Model, db
from models.local_provider_event import LocalProviderEventType
from utils.date import get_dept_timezone

DIGITAL_PROJECTION = 'DIGITAL'
DUBBED_VERSION = 'DUBBED'
LOCAL_VERSION = 'LOCAL'
ORIGINAL_VERSION = 'ORIGINAL'
FRENCH_VERSION_SUFFIX = 'VF'
ORIGINAL_VERSION_SUFFIX = 'VO'


class AllocineStocks(LocalProvider):
    name = "Allociné"
    can_create = True
    manually_editable_fields = ['available', 'price', 'bookingLimitDatetime']

    def __init__(self, venue_provider: VenueProvider):
        super().__init__(venue_provider)
        self.api_key = os.environ.get('ALLOCINE_API_KEY', None)
        self.venue = venue_provider.venue
        self.theater_id = venue_provider.venueIdAtOfferProvider
        self.movies_showtimes = get_movies_showtimes(self.api_key, self.theater_id)

        self.movie_information = None
        self.filtered_movie_showtimes = None
        self.last_product_id = None
        self.last_vf_offer_id = None
        self.last_vo_offer_id = None

    def __next__(self) -> List[ProvidableInfo]:
        raw_movie_information = next(self.movies_showtimes)
        try:
            self.movie_information = retrieve_movie_information(raw_movie_information['node']['movie'])
            self.filtered_movie_showtimes = _filter_only_digital_and_non_experience_showtimes(raw_movie_information
                                                                                              ['node']['showtimes'])
            showtimes_number = len(self.filtered_movie_showtimes)

        except KeyError:
            self.log_provider_event(LocalProviderEventType.SyncError,
                                    f"Error parsing information for movie: {raw_movie_information['node']['movie']}")
            return []

        providable_information_list = [self.create_providable_info(Product,
                                                                   self.movie_information['id'],
                                                                   datetime.utcnow())]

        if _has_original_version_product(self.filtered_movie_showtimes):
            venue_movie_original_version_unique_id = _build_original_movie_uuid(self.movie_information, self.venue)
            original_version_offer_providable_information = self.create_providable_info(Offer,
                                                                                        venue_movie_original_version_unique_id,
                                                                                        datetime.utcnow())

            providable_information_list.append(original_version_offer_providable_information)

        if _has_french_version_product(self.filtered_movie_showtimes):
            venue_movie_french_version_unique_id = _build_french_movie_uuid(self.movie_information, self.venue)
            french_version_offer_providable_information = self.create_providable_info(Offer,
                                                                                      venue_movie_french_version_unique_id,
                                                                                      datetime.utcnow())
            providable_information_list.append(french_version_offer_providable_information)

        for showtime_number in range(showtimes_number):
            showtime = self.filtered_movie_showtimes[showtime_number]
            id_at_providers = _build_stock_uuid(self.movie_information, self.venue, showtime)

            stock_providable_information = self.create_providable_info(Stock,
                                                                       id_at_providers,
                                                                       datetime.utcnow())
            providable_information_list.append(stock_providable_information)

        return providable_information_list

    def fill_object_attributes(self, pc_object: Model):
        if isinstance(pc_object, Product):
            self.fill_product_attributes(pc_object)

        if isinstance(pc_object, Offer):
            self.fill_offer_attributes(pc_object)

        if isinstance(pc_object, Stock):
            self.fill_stock_attributes(pc_object)

    def fill_product_attributes(self, allocine_product: Product):
        allocine_product.thumbCount = 0
        allocine_product.description = self.movie_information['description']
        allocine_product.durationMinutes = self.movie_information['duration']
        if not allocine_product.extraData:
            allocine_product.extraData = {}
        if 'visa' in self.movie_information:
            allocine_product.extraData["visa"] = self.movie_information['visa']
        if 'stageDirector' in self.movie_information:
            allocine_product.extraData["stageDirector"] = self.movie_information['stageDirector']
        allocine_product.name = self.movie_information['title']

        allocine_product.type = str(EventType.CINEMA)
        is_new_product_to_insert = allocine_product.id is None

        if is_new_product_to_insert:
            allocine_product.id = get_next_product_id_from_database()
        self.last_product_id = allocine_product.id

    def fill_offer_attributes(self, allocine_offer: Offer):
        allocine_offer.venueId = self.venue.id
        allocine_offer.bookingEmail = self.venue.bookingEmail
        allocine_offer.description = self.movie_information['description']
        allocine_offer.durationMinutes = self.movie_information['duration']
        if not allocine_offer.extraData:
            allocine_offer.extraData = {}
        if 'visa' in self.movie_information:
            allocine_offer.extraData["visa"] = self.movie_information['visa']
        if 'stageDirector' in self.movie_information:
            allocine_offer.extraData["stageDirector"] = self.movie_information['stageDirector']

        movie_version = ORIGINAL_VERSION_SUFFIX if _is_original_version_offer(allocine_offer.idAtProviders) \
            else FRENCH_VERSION_SUFFIX

        allocine_offer.name = f"{self.movie_information['title']} - {movie_version}"
        allocine_offer.type = str(EventType.CINEMA)
        allocine_offer.productId = self.last_product_id

        is_new_offer_to_insert = allocine_offer.id is None

        if is_new_offer_to_insert:
            allocine_offer.id = get_next_offer_id_from_database()

        if not is_new_offer_to_insert:
            if 'isDuo' not in allocine_offer.fieldsUpdated:
                allocine_offer.isDuo = False

        if movie_version == ORIGINAL_VERSION_SUFFIX:
            self.last_vo_offer_id = allocine_offer.id
        else:
            self.last_vf_offer_id = allocine_offer.id

    def fill_stock_attributes(self, allocine_stock: Stock):

        showtime_uuid = _get_showtimes_uuid_by_idAtProvider(allocine_stock.idAtProviders)
        showtime = _find_showtime_by_showtime_uuid(self.filtered_movie_showtimes, showtime_uuid)

        parsed_showtimes = retrieve_showtime_information(showtime)
        diffusion_version = parsed_showtimes['diffusionVersion']

        allocine_stock.offerId = self.last_vo_offer_id if diffusion_version == ORIGINAL_VERSION else \
            self.last_vf_offer_id

        local_tz = get_dept_timezone(self.venue.departementCode)
        date_in_utc = _format_date_from_local_timezone_to_utc(parsed_showtimes['startsAt'], local_tz)
        allocine_stock.beginningDatetime = date_in_utc

        is_new_stock_to_insert = allocine_stock.id is None
        if is_new_stock_to_insert:
            allocine_stock.fieldsUpdated = []

        if 'bookingLimitDatetime' not in allocine_stock.fieldsUpdated:
            allocine_stock.bookingLimitDatetime = date_in_utc

        if 'available' not in allocine_stock.fieldsUpdated:
            allocine_stock.available = None

        if 'price' not in allocine_stock.fieldsUpdated:
            allocine_stock.price = self.apply_allocine_price_rule(allocine_stock)

        movie_duration = self.movie_information['duration']
        stock_movie_duration = timedelta(minutes=movie_duration) if movie_duration else timedelta(seconds=1)
        allocine_stock.endDatetime = allocine_stock.beginningDatetime + stock_movie_duration

    def apply_allocine_price_rule(self, allocine_stock: Stock) -> int:
        price = None
        for price_rule in self.venue_provider.priceRules:
            if price_rule.priceRule(allocine_stock):
                return price_rule.price
        if not price:
            raise AllocineStocksPriceRule("Aucun prix par défaut n'a été trouvé")

    def get_object_thumb(self) -> bytes:
        if 'poster_url' in self.movie_information:
            image_url = self.movie_information['poster_url']
            return get_movie_poster(image_url)
        return super().get_object_thumb()

    def get_object_thumb_index(self) -> int:
        return 1


def get_next_product_id_from_database():
    sequence = Sequence('product_id_seq')
    return db.session.execute(sequence)


def get_next_offer_id_from_database():
    sequence = Sequence('offer_id_seq')
    return db.session.execute(sequence)


def retrieve_movie_information(raw_movie_information: Dict) -> Dict:
    parsed_movie_information = dict()
    parsed_movie_information['id'] = raw_movie_information['id']
    parsed_movie_information['description'] = _build_description(raw_movie_information)
    parsed_movie_information['duration'] = _parse_movie_duration(raw_movie_information['runtime'])
    parsed_movie_information['title'] = raw_movie_information['title']
    if raw_movie_information['poster']:
        parsed_movie_information['poster_url'] = _format_poster_url(raw_movie_information['poster']['url'])
    is_stage_director_info_available = len(raw_movie_information['credits']['edges']) > 0

    if is_stage_director_info_available:
        parsed_movie_information['stageDirect' \
                                 'or'] = _build_stage_director_full_name(raw_movie_information)

    is_operating_visa_available = len(raw_movie_information['releases']) > 0 \
                                  and len(raw_movie_information['releases'][0]['data']) > 0

    if is_operating_visa_available:
        parsed_movie_information['visa'] = _get_operating_visa(raw_movie_information)

    return parsed_movie_information


def retrieve_showtime_information(showtime_information: Dict) -> Dict:
    return {
        'startsAt': parse(showtime_information['startsAt']),
        'diffusionVersion': showtime_information['diffusionVersion'],
        'projection': showtime_information['projection'][0],
        'experience': showtime_information['experience']
    }


def _filter_only_digital_and_non_experience_showtimes(showtimes_information: List[Dict]) -> List[Dict]:
    return list(filter(lambda showtime: showtime['projection'][0] == DIGITAL_PROJECTION and
                                        showtime['experience'] is None, showtimes_information))


def _find_showtime_by_showtime_uuid(showtimes: List[Dict], showtime_uuid: str) -> Union[Dict, None]:
    for showtime in showtimes:
        if _build_showtime_uuid(showtime) == showtime_uuid:
            return showtime
    return None


def _format_date_from_local_timezone_to_utc(date: datetime, local_tz: str) -> datetime:
    from_zone = tz.gettz(local_tz)
    to_zone = tz.gettz('UTC')
    date_in_tz = date.replace(tzinfo=from_zone)
    return date_in_tz.astimezone(to_zone)


def _get_showtimes_uuid_by_idAtProvider(id_at_provider: str):
    return id_at_provider.split('#')[1]


def _build_description(movie_info: Dict) -> str:
    allocine_movie_url = movie_info['backlink']['url'].replace("\\", "")
    return f"{movie_info['synopsis']}\n{movie_info['backlink']['label']}: {allocine_movie_url}"


def _format_poster_url(url: str) -> str:
    return url.replace("\/", "/")


def _get_operating_visa(movie_info: Dict) -> Optional[str]:
    return movie_info['releases'][0]['data']['visa_number']


def _build_stage_director_full_name(movie_info: Dict) -> str:
    stage_director_first_name = movie_info['credits']['edges'][0]['node']['person']['firstName']
    stage_director_last_name = movie_info['credits']['edges'][0]['node']['person']['lastName']
    return f"{stage_director_first_name} {stage_director_last_name}"


def _parse_movie_duration(duration: str) -> Optional[int]:
    if not duration:
        return None
    hours_minutes = "([0-9]+)H([0-9]+)"
    duration_regex = re.compile(hours_minutes)
    match = duration_regex.search(duration)
    movie_duration_hours = int(match.groups()[0])
    movie_duration_minutes = int(match.groups()[1])
    return movie_duration_hours * 60 + movie_duration_minutes


def _has_original_version_product(movies_showtimes: List[Dict]) -> bool:
    return ORIGINAL_VERSION in list(map(lambda movie: movie['diffusionVersion'], movies_showtimes))


def _has_french_version_product(movies_showtimes: List[Dict]) -> bool:
    movies = list(map(lambda movie: movie['diffusionVersion'], movies_showtimes))
    return LOCAL_VERSION in movies or DUBBED_VERSION in movies


def _is_original_version_offer(id_at_providers: str) -> bool:
    return id_at_providers[-3:] == f"-{ORIGINAL_VERSION_SUFFIX}"


def _build_movie_uuid(movie_information: Dict, venue: Venue) -> str:
    return f"{movie_information['id']}%{venue.siret}"


def _build_french_movie_uuid(movie_information: Dict, venue: Venue) -> str:
    return f"{_build_movie_uuid(movie_information, venue)}-{FRENCH_VERSION_SUFFIX}"


def _build_original_movie_uuid(movie_information: Dict, venue: Venue) -> str:
    return f"{_build_movie_uuid(movie_information, venue)}-{ORIGINAL_VERSION_SUFFIX}"


def _build_showtime_uuid(showtime_details: Dict) -> str:
    return f"{showtime_details['diffusionVersion']}/{showtime_details['startsAt']}"


def _build_stock_uuid(movie_information: Dict, venue: Venue, showtime_details: Dict) -> str:
    return f"{_build_movie_uuid(movie_information, venue)}#{_build_showtime_uuid(showtime_details)}"
