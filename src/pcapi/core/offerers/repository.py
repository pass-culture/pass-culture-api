from typing import Optional

from pcapi.core.offerers.models import Offerer
from pcapi.core.offerers.models import Venue
from pcapi.core.offerers.models import VenueLabel
from pcapi.core.users.models import User
from pcapi.models.user_offerer import UserOfferer


def get_all_venue_labels() -> list[VenueLabel]:
    return VenueLabel.query.all()


def get_all_offerers_for_user(user: User, filters: dict) -> list[Offerer]:
    query = Offerer.query.filter(Offerer.isActive.is_(True))

    if not user.isAdmin:
        query = query.join(UserOfferer, UserOfferer.offererId == Offerer.id).filter(UserOfferer.userId == user.id)

    if "validated" in filters and filters["validated"] is not None:
        if filters["validated"] == True:
            query = query.filter(Offerer.validationToken.is_(None))
        else:
            query = query.filter(Offerer.validationToken.isnot(None))

    if "validated_for_user" in filters and filters["validated_for_user"] is not None:
        if filters["validated_for_user"] == True:
            query = query.filter(UserOfferer.validationToken.is_(None))
        else:
            query = query.filter(UserOfferer.validationToken.isnot(None))

    return query.all()


def get_filtered_venues(
    pro_user_id: int,
    user_is_admin: bool,
    active_offerers_only: Optional[bool] = False,
    offerer_id: Optional[int] = None,
    validated_offerer: Optional[bool] = None,
    validated_offerer_for_user: Optional[bool] = None,
) -> list[Venue]:
    query = Venue.query.join(Offerer, Offerer.id == Venue.managingOffererId).join(
        UserOfferer, UserOfferer.offererId == Offerer.id
    )
    if not user_is_admin:
        query = query.filter(UserOfferer.userId == pro_user_id)

    if validated_offerer is not None:
        if validated_offerer:
            query = query.filter(Offerer.validationToken.is_(None))
        else:
            query = query.filter(Offerer.validationToken.isnot(None))
    if validated_offerer_for_user is not None:
        if validated_offerer_for_user:
            query = query.filter(UserOfferer.validationToken.is_(None))
        else:
            query = query.filter(UserOfferer.validationToken.isnot(None))

    if active_offerers_only:
        query = query.filter(Offerer.isActive.is_(True))

    if offerer_id:
        query = query.filter(Venue.managingOffererId == offerer_id)

    return query.order_by(Venue.name).all()
