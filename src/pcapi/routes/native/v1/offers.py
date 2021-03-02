from typing import Optional

from pcapi.core.bookings.api import has_user_enough_credit_book
from pcapi.core.offers.models import Offer
from pcapi.core.users.models import User
from pcapi.routes.native.security import authenticated_user_optional
from pcapi.serialization.decorator import spectree_serialize

from . import blueprint
from .serialization import offers as serializers


@blueprint.native_v1.route("/offer/<int:offer_id>", methods=["GET"])
@authenticated_user_optional
@spectree_serialize(
    response_model=serializers.OfferResponse, api=blueprint.api, on_error_statuses=[404]
)  # type: ignore
def get_offer(user: Optional[User], offer_id: str) -> serializers.OfferResponse:
    offer = Offer.query.filter_by(id=offer_id).first_or_404()

    if user:
        for stock in offer.stocks:
            stock.hasUserEnoughCreditToBook = has_user_enough_credit_book(user, stock.price, offer)

    return serializers.OfferResponse.from_orm(offer)
