from flask import jsonify
from flask import request
from flask_login import current_user
from flask_login import login_required

from pcapi.core.bookings.repository import get_active_bookings_quantity_for_venue
from pcapi.core.bookings.repository import get_validated_bookings_quantity_for_venue
from pcapi.core.offerers import api as offerers_api
from pcapi.core.offerers import repository as offerers_repository
from pcapi.core.offerers.models import Venue
from pcapi.core.offerers.validation import validate_coordinates
from pcapi.core.offers.repository import get_active_offers_count_for_venue
from pcapi.core.offers.repository import get_sold_out_offers_count_for_venue
from pcapi.flask_app import private_api
from pcapi.repository import repository
from pcapi.routes.serialization import as_dict
from pcapi.routes.serialization.venues_serialize import EditVenueBodyModel
from pcapi.routes.serialization.venues_serialize import GetVenueListResponseModel
from pcapi.routes.serialization.venues_serialize import GetVenueResponseModel
from pcapi.routes.serialization.venues_serialize import PostVenueBodyModel
from pcapi.routes.serialization.venues_serialize import VenueListItemResponseModel
from pcapi.routes.serialization.venues_serialize import VenueListQueryModel
from pcapi.routes.serialization.venues_serialize import VenueResponseModel
from pcapi.routes.serialization.venues_serialize import VenueStatsResponseModel
from pcapi.serialization.decorator import spectree_serialize
from pcapi.use_cases.create_venue import create_venue
from pcapi.utils.includes import VENUE_INCLUDES
from pcapi.utils.rest import check_user_has_access_to_offerer
from pcapi.utils.rest import expect_json_data
from pcapi.utils.rest import load_or_404


@private_api.route("/venues/<venue_id>", methods=["GET"])
@login_required
@spectree_serialize(response_model=GetVenueResponseModel)
def get_venue(venue_id: str) -> GetVenueResponseModel:
    venue = load_or_404(Venue, venue_id)
    check_user_has_access_to_offerer(current_user, venue.managingOffererId)

    return GetVenueResponseModel.from_orm(venue)


@private_api.route("/venues", methods=["GET"])
@login_required
@spectree_serialize(response_model=GetVenueListResponseModel)
def get_venues(query: VenueListQueryModel) -> GetVenueListResponseModel:
    venue_list = offerers_repository.get_filtered_venues(
        pro_user_id=current_user.id,
        user_is_admin=current_user.isAdmin,
        active_offerers_only=query.active_offerers_only,
        offerer_id=query.offerer_id,
        validated_offerer=query.validated,
        validated_offerer_for_user=query.validated_for_user,
    )

    return GetVenueListResponseModel(
        venues=[
            VenueListItemResponseModel(
                id=venue.id,
                managingOffererId=venue.managingOfferer.id,
                name=venue.name,
                offererName=venue.managingOfferer.name,
                publicName=venue.publicName,
                isVirtual=venue.isVirtual,
                bookingEmail=venue.bookingEmail,
            )
            for venue in venue_list
        ]
    )


# @debt api-migration
@private_api.route("/venues", methods=["POST"])
@login_required
@spectree_serialize(response_model=VenueResponseModel, on_success_status=201)  # type: ignore
def post_create_venue(body: PostVenueBodyModel) -> VenueResponseModel:
    validate_coordinates(body.latitude, body.longitude)

    venue = create_venue(venue_properties=body.dict(), save=repository.save)

    return VenueResponseModel.from_orm(venue)


@private_api.route("/venues/<venue_id>", methods=["PATCH"])
@login_required
@spectree_serialize(response_model=GetVenueResponseModel)
def edit_venue(venue_id: str, body: EditVenueBodyModel) -> GetVenueResponseModel:
    venue = load_or_404(Venue, venue_id)

    check_user_has_access_to_offerer(current_user, venue.managingOffererId)
    venue = offerers_api.update_venue(venue, **body.dict(exclude_unset=True))

    return GetVenueResponseModel.from_orm(venue)


@private_api.route("/venues/<humanized_venue_id>/stats", methods=["GET"])
@login_required
@spectree_serialize(on_success_status=200, response_model=VenueStatsResponseModel)
def get_venue_stats(humanized_venue_id: str) -> VenueStatsResponseModel:
    venue = load_or_404(Venue, humanized_venue_id)
    check_user_has_access_to_offerer(current_user, venue.managingOffererId)

    active_bookings_quantity = get_active_bookings_quantity_for_venue(venue.id)
    validated_bookings_count = get_validated_bookings_quantity_for_venue(venue.id)
    active_offers_count = get_active_offers_count_for_venue(venue.id)
    sold_out_offers_count = get_sold_out_offers_count_for_venue(venue.id)

    return VenueStatsResponseModel(
        activeBookingsQuantity=active_bookings_quantity,
        validatedBookingsQuantity=validated_bookings_count,
        activeOffersCount=active_offers_count,
        soldOutOffersCount=sold_out_offers_count,
    )
