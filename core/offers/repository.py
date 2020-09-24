from sqlalchemy.orm import joinedload

import domain.expenses
from models.db import db
from models.user_sql_entity import UserSQLEntity

from . import models


def get_booking_by_id(booking_id):
    # FIXME: the repository should rather raise a DoesNotExist error.
    # The error should get caught by the route, which would return a
    # 404 response.
    return models.Booking.query.filter_by(id=booking_id).first_or_404()


def has_user_already_booked_offer(user, offer):
    return (
        db.query(
            models.Booking.query
            .filter_by(
                userId=user.id,
                isCancelled=False,
            )
            .join(models.Stock)
            .filter_by(models.Stock.offerId == offer.id)
            .exists()
        )
        .scalar()
    )


def get_user_expenses(user: UserSQLEntity) -> dict:
    """Return the user's expenses and limits.

    The returned dict looks like::

        {
            'all': {'max': 500, 'actual': 190},
            'physical': {'max': 200, 'actual': 180},
            'digital': {'max': 300, 'actual': 10},
        }
    """
    bookings = (
        models.Booking.query
        .filter_by(user=user)
        .filter_by(isCancelled=False)
        .options(
            joinedload(models.Booking.stock).
            joinedload(models.Stock.offer)
        )
        .all()
    )
    return domain.expenses.get_expenses(bookings)
