import logging

from pcapi.routes.adage.security import adage_api_key_required
from pcapi.routes.adage.v1.serialization.prebooking import GetPreBookingsRequest
from pcapi.routes.adage.v1.serialization.prebooking import PreBookingResponse
from pcapi.routes.adage.v1.serialization.prebooking import PreBookingsResponse
from pcapi.serialization.decorator import spectree_serialize


logger = logging.getLogger(__name__)

from . import blueprint


@blueprint.adage_v1.route("/prebookings", methods=["GET"])
@spectree_serialize(api=blueprint.api, response_model=PreBookingsResponse)
@adage_api_key_required
def get_pre_bookings(query: GetPreBookingsRequest) -> PreBookingsResponse:
    pass


@blueprint.adage_v1.route("/prebookings/<int:pre_booking_id>", methods=["GET"])
@spectree_serialize(api=blueprint.api, response_model=PreBookingResponse)
@adage_api_key_required
def get_pre_booking() -> PreBookingResponse:
    pass
