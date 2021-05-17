from datetime import datetime
from typing import Optional
from typing import Union

from pydantic import BaseModel

from pcapi.serialization.utils import dehumanize_field
from pcapi.serialization.utils import humanize_field
from pcapi.serialization.utils import string_to_boolean_field
from pcapi.serialization.utils import to_camel
from pcapi.utils.date import format_into_utc_date


class PostVenueBodyModel(BaseModel):
    address: str
    bookingEmail: str
    city: str
    comment: Optional[str]
    latitude: float
    longitude: float
    managingOffererId: str
    name: str
    publicName: Optional[str]
    postalCode: str
    siret: str
    venueLabelId: str
    venueTypeId: str


class VenueResponseModel(BaseModel):
    id: str

    _humanize_id = humanize_field("id")

    class Config:
        orm_mode = True
        allow_population_by_field_name = True
        arbitrary_types_allowed = True


class VenueStatsResponseModel(BaseModel):
    activeBookingsQuantity: int
    validatedBookingsQuantity: int
    activeOffersCount: int
    soldOutOffersCount: int


class GetVenueManagingOffererResponseModel(BaseModel):
    address: Optional[str]
    bic: Optional[str]
    city: str
    dateCreated: datetime
    dateModifiedAtLastProvider: Optional[datetime]
    demarchesSimplifieesApplicationId: Optional[str]
    fieldsUpdated: list[str]
    iban: Optional[str]
    id: str
    idAtProviders: Optional[str]
    isValidated: bool
    lastProviderId: Optional[str]
    name: str
    postalCode: str
    # FIXME (dbaty, 2020-11-09): optional until we populate the database (PC-5693)
    siren: Optional[str]

    _humanize_id = humanize_field("id")

    class Config:
        orm_mode = True
        json_encoders = {datetime: format_into_utc_date}


class GetVenueResponseModel(BaseModel):
    address: Optional[str]
    bic: Optional[str]
    bookingEmail: Optional[str]
    city: Optional[str]
    comment: Optional[str]
    dateCreated: datetime
    dateModifiedAtLastProvider: Optional[datetime]
    demarchesSimplifieesApplicationId: Optional[str]
    departementCode: Optional[str]
    fieldsUpdated: list[str]
    iban: Optional[str]
    id: str
    idAtProviders: Optional[str]
    isValidated: bool
    isVirtual: bool
    lastProviderId: Optional[str]
    latitude: Optional[float]
    longitude: Optional[float]
    managingOfferer: GetVenueManagingOffererResponseModel
    managingOffererId: str
    name: str
    postalCode: Optional[str]
    publicName: Optional[str]
    siret: Optional[str]
    venueLabelId: Optional[str]
    venueTypeId: Optional[str]

    _humanize_id = humanize_field("id")
    _humanize_managing_offerer_id = humanize_field("managingOffererId")
    _humanize_venue_label_id = humanize_field("venueLabelId")
    _humanize_venue_type_id = humanize_field("venueTypeId")

    class Config:
        orm_mode = True
        json_encoders = {datetime: format_into_utc_date}


class EditVenueBodyModel(BaseModel):
    name: Optional[str]
    address: Optional[str]
    siret: Optional[str]
    latitude: Optional[Union[float, str]]
    longitude: Optional[Union[float, str]]
    bookingEmail: Optional[str]
    postalCode: Optional[str]
    city: Optional[str]
    publicName: Optional[str]
    comment: Optional[str]
    venueTypeId: Optional[int]
    venueLabelId: Optional[int]

    _dehumanize_venue_label_id = dehumanize_field("venueLabelId")
    _dehumanize_venue_type_id = dehumanize_field("venueTypeId")


class VenueListItemResponseModel(BaseModel):
    id: str
    managingOffererId: str
    name: str
    offererName: str
    publicName: Optional[str]
    isVirtual: bool
    bookingEmail: Optional[str]

    _humanize_id = humanize_field("id")
    _humanize_managing_offerer_id = humanize_field("managingOffererId")


class GetVenueListResponseModel(BaseModel):
    venues: list[VenueListItemResponseModel]


class VenueListQueryModel(BaseModel):
    validated_for_user: Optional[bool]
    validated: Optional[bool]
    active_offerers_only: Optional[bool]
    offerer_id: Optional[int]

    _dehumanize_offerer_id = dehumanize_field("offerer_id")
    _string_to_boolean_validated_for_user = string_to_boolean_field("validated_for_user")
    _string_to_boolean_validated = string_to_boolean_field("validated")
    _string_to_boolean_active_offerers_only = string_to_boolean_field("active_offerers_only")

    class Config:
        alias_generator = to_camel
        extra = "forbid"
