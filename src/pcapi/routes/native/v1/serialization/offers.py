from datetime import datetime
from decimal import Decimal
from typing import Callable
from typing import Dict
from typing import List
from typing import Optional

from pydantic import BaseModel
from pydantic.class_validators import validator
from pydantic.fields import Field

from pcapi.domain.music_types import MUSIC_SUB_TYPES_DICT
from pcapi.domain.music_types import MUSIC_TYPES_DICT
from pcapi.domain.show_types import SHOW_SUB_TYPES_DICT
from pcapi.domain.show_types import SHOW_TYPES_DICT
from pcapi.models.offer_type import CategoryNameEnum
from pcapi.models.offer_type import CategoryType
from pcapi.utils.logger import logger


class Coordinates(BaseModel):
    latitude: Optional[Decimal] = Field(..., nullable=True)
    longitude: Optional[Decimal] = Field(..., nullable=True)


class OfferCategoryResponse(BaseModel):
    categoryType: CategoryType
    label: str
    name: Optional[CategoryNameEnum] = Field(..., nullable=True)


class OfferOffererResponse(BaseModel):
    name: str

    class Config:
        orm_mode = True


class OfferStockResponse(BaseModel):
    id: int
    beginningDatetime: Optional[datetime] = Field(..., nullable=True)
    bookingLimitDatetime: Optional[datetime] = Field(..., nullable=True)
    isBookable: bool
    price: Decimal

    class Config:
        orm_mode = True


class OfferVenueResponse(BaseModel):
    @classmethod
    def from_orm(cls, venue):  # type: ignore
        venue.coordinates = {"latitude": venue.latitude, "longitude": venue.longitude}
        return super().from_orm(venue)

    id: int
    address: Optional[str] = Field(..., nullable=True)
    city: Optional[str] = Field(..., nullable=True)
    managingOfferer: OfferOffererResponse = Field(..., alias="offerer")
    name: str
    postalCode: Optional[str] = Field(..., nullable=True)
    publicName: Optional[str] = Field(..., nullable=True)
    coordinates: Coordinates

    class Config:
        orm_mode = True
        allow_population_by_field_name = True


LABELS_BY_DICT_MAPPING = {"musicSubType": ""}


def get_id_converter(labels_by_id: Dict, field_name: str) -> Callable[[Optional[str]], Optional[str]]:
    def convert_id_into_label(value_id: Optional[str]) -> Optional[str]:
        try:
            return labels_by_id[int(value_id)] if value_id else None
        except ValueError:  # on the second time this function is called twice, the field is already converted
            return None
        except KeyError:
            logger.exception("Invalid '%s' '%s' found on an offer", field_name, value_id)
            return None

    return convert_id_into_label


class OfferExtraData(BaseModel):
    author: Optional[str]
    durationMinutes: Optional[int] = Field(..., nullable=True)
    isbn: Optional[str]
    musicSubType: Optional[str]
    musicType: Optional[str]
    performer: Optional[str]
    showSubType: Optional[str]
    showType: Optional[str]
    stageDirector: Optional[str]
    speaker: Optional[str]
    visa: Optional[str]

    _convert_music_sub_type = validator("musicSubType", pre=True, allow_reuse=True)(
        get_id_converter(MUSIC_SUB_TYPES_DICT, "musicSubType")
    )
    _convert_music_type = validator("musicType", pre=True, allow_reuse=True)(
        get_id_converter(MUSIC_TYPES_DICT, "musicType")
    )
    _convert_show_sub_type = validator("showSubType", pre=True, allow_reuse=True)(
        get_id_converter(SHOW_SUB_TYPES_DICT, "showSubType")
    )
    _convert_show_type = validator("showType", pre=True, allow_reuse=True)(
        get_id_converter(SHOW_TYPES_DICT, "showType")
    )


class OfferAccessibilityResponse(BaseModel):
    audioDisability: Optional[bool] = Field(..., nullable=True)
    mentalDisability: Optional[bool] = Field(..., nullable=True)
    motorDisability: Optional[bool] = Field(..., nullable=True)
    visualDisability: Optional[bool] = Field(..., nullable=True)


class OfferImageResponse(BaseModel):
    url: str
    credit: Optional[str] = Field(..., nullable=True)

    class Config:
        orm_mode = True


class OfferResponse(BaseModel):
    @classmethod
    def from_orm(cls, offer):  # type: ignore
        offer.category = {
            "name": offer.offer_category,
            "label": offer.offerType["appLabel"],
            "categoryType": offer.category_type,
        }
        offer.accessibility = {
            "audioDisability": offer.audioDisabilityCompliant,
            "mentalDisability": offer.mentalDisabilityCompliant,
            "motorDisability": offer.motorDisabilityCompliant,
            "visualDisability": offer.visualDisabilityCompliant,
        }

        if offer.extraData:
            offer.extraData["durationMinutes"] = offer.durationMinutes
        else:
            offer.extraData = {"durationMinutes": offer.durationMinutes}

        return super().from_orm(offer)

    id: int
    accessibility: OfferAccessibilityResponse
    description: Optional[str] = Field(..., nullable=True)
    externalTicketOfficeUrl: Optional[str] = Field(..., nullable=True)
    extraData: OfferExtraData
    isActive: bool
    isDigital: bool
    isDuo: bool
    name: str
    category: OfferCategoryResponse
    stocks: List[OfferStockResponse]
    image: Optional[OfferImageResponse] = Field(..., nullable=True)
    venue: OfferVenueResponse
    withdrawalDetails: Optional[str] = Field(..., nullable=True)

    class Config:
        orm_mode = True
        allow_population_by_field_name = True
