from datetime import datetime
from typing import Optional
from typing import Union

from pydantic import BaseModel
from pydantic import Field
from pydantic import condecimal
from pydantic import validator

from pcapi.serialization.utils import dehumanize_field
from pcapi.serialization.utils import humanize_field
from pcapi.serialization.utils import to_camel
from pcapi.utils.date import format_into_utc_date


class StockResponseModel(BaseModel):
    beginningDatetime: Optional[datetime]
    bookingLimitDatetime: Optional[datetime]
    dnBookedQuantity: int = Field(alias="bookingsQuantity")
    dateCreated: datetime
    dateModified: datetime
    id: str
    isEventDeletable: bool
    isEventExpired: bool
    offerId: str
    price: float
    quantity: Optional[int]

    _humanize_id = humanize_field("id")
    _humanize_offer_id = humanize_field("offerId")

    class Config:
        allow_population_by_field_name = True
        json_encoders = {datetime: format_into_utc_date}
        orm_mode = True


class StocksResponseModel(BaseModel):
    stocks: list[StockResponseModel]

    class Config:
        json_encoders = {datetime: format_into_utc_date}


class StockCreationBodyModel(BaseModel):
    beginning_datetime: Optional[datetime]
    booking_limit_datetime: Optional[datetime]
    price: float
    quantity: Optional[int]

    class Config:
        alias_generator = to_camel
        extra = "forbid"


class StockEditionBodyModel(BaseModel):
    beginning_datetime: Optional[datetime]
    booking_limit_datetime: Optional[datetime]
    id: int
    price: float
    quantity: Optional[int]

    _dehumanize_id = dehumanize_field("id")

    class Config:
        alias_generator = to_camel
        extra = "forbid"


class StockIdResponseModel(BaseModel):
    id: str

    _humanize_stock_id = humanize_field("id")

    class Config:
        orm_mode = True
        allow_population_by_field_name = True
        arbitrary_types_allowed = True


class StocksUpsertBodyModel(BaseModel):
    offer_id: int
    stocks: list[Union[StockCreationBodyModel, StockEditionBodyModel]]

    _dehumanize_offer_id = dehumanize_field("offer_id")

    class Config:
        alias_generator = to_camel


class StockIdsResponseModel(BaseModel):
    stockIds: list[StockIdResponseModel]


class UpdateVenueStockBodyModel(BaseModel):
    """Available stock quantity for a book"""

    ref: str = Field(title="ISBN", description="Format: EAN13")
    available: int
    price: condecimal(decimal_places=2) = Field(None, description="prix en Euros avec 2 décimales possibles")

    @validator("price", pre=True)
    def empty_string_price_casted_to_none(cls, v):  # pylint: disable=no-self-argument
        # Performed before Pydantic validators to catch empty strings but will not get "0"
        if not v:
            return None
        return v

    @validator("price")
    def zero_price_casted_to_none(cls, v):  # pylint: disable=no-self-argument
        # Performed before Pydantic validators to catch empty strings but will not get "0"
        if not v:
            return None
        return v

    class Config:
        title = "Stock"


class UpdateVenueStocksBodyModel(BaseModel):
    stocks: list[UpdateVenueStockBodyModel]

    class Config:
        title = "Venue's stocks update body"
