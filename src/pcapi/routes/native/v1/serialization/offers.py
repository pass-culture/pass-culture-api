from datetime import datetime
from decimal import Decimal
from typing import List
from typing import Optional

from pydantic import BaseModel
from pydantic.fields import Field


class OfferCategoryResponse(BaseModel):
    appLabel: str = Field(..., alias="label")
    value: str

    class Config:
        allow_population_by_field_name = True


class OfferOffererResponse(BaseModel):
    name: str

    class Config:
        orm_mode = True


class OfferStockResponse(BaseModel):
    id: int
    beginningDatetime: Optional[datetime]
    price: Decimal

    class Config:
        orm_mode = True


class OfferVenueResponse(BaseModel):
    id: int
    address: Optional[str]
    city: Optional[str]
    managingOfferer: OfferOffererResponse = Field(..., alias="offerer")
    name: str
    postalCode: Optional[str]
    publicName: Optional[str]

    class Config:
        orm_mode = True
        allow_population_by_field_name = True


class OfferResponse(BaseModel):
    id: int
    description: Optional[str]
    isDigital: bool
    isDuo: bool
    name: str
    offerType: OfferCategoryResponse = Field(..., alias="category")
    bookableStocks: List[OfferStockResponse]
    thumbUrl: Optional[str] = Field(None, alias="imageUrl")
    venue: OfferVenueResponse
    withdrawalDetails: Optional[str]

    class Config:
        orm_mode = True
        allow_population_by_field_name = True
