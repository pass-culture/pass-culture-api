import enum
import typing

from pcapi.core.offerers import models as offerers_models
from pcapi.core.offerers.models import VenueTypeEnum as VenueTypeBaseEnum
from pcapi.serialization.utils import to_camel

from . import BaseModel


# this dynamically build class should not be used elsewhere,
# its only purpose is to help the openapi build.
VenueTypeEnum = enum.Enum("VenueTypeEnum", {code: code for code in VenueTypeBaseEnum.get_codes()})  # type: ignore


class VenueResponse(BaseModel):
    class Config:
        orm_mode = True
        alias_generator = to_camel
        allow_population_by_field_name = True

    id: int
    name: str
    latitude: typing.Optional[float]
    longitude: typing.Optional[float]
    city: typing.Optional[str]
    publicName: typing.Optional[str]
    isVirtual: bool
    isPermanent: typing.Optional[bool]
    withdrawalDetails: typing.Optional[str]
    address: typing.Optional[str]
    postalCode: typing.Optional[str]
    venueTypeEnum: VenueTypeEnum

    @classmethod
    def from_orm(cls, venue: offerers_models.Venue) -> "VenueResponse":
        try:
            venue_type_enum = getattr(VenueTypeEnum, venue.venueType.code)
        except (AttributeError, TypeError):
            venue_type_enum = VenueTypeEnum.OTHER  # type: ignore

        venue.venueTypeEnum = venue_type_enum
        return super().from_orm(venue)
