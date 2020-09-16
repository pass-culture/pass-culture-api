from flask import current_app as app
from sqlalchemy.orm import joinedload

from connectors import redis
import domain.expenses
from models.booking_sql_entity import BookingSQLEntity
from models.db import db
from models.feature import FeatureToggle
from models.recommendation import Recommendation
from models.stock_sql_entity import StockSQLEntity
from models.user_sql_entity import UserSQLEntity
from repository import feature_queries
from utils.mailing import send_raw_email
from utils.token import random_token
from infrastructure.services.notification.mailjet_notification_service import MailjetNotificationService

from . import validation


def book_offer(
    beneficiary: UserSQLEntity,
    stock: StockSQLEntity,
    quantity: int,
    recommendation: Recommendation,
) -> BookingSQLEntity:
    """Return a booking or raise an exception if it's not possible."""
    validation.check_can_book_free_offer(beneficiary, stock)
    validation.check_offer_already_booked(beneficiary, stock.offer)
    validation.check_quantity(stock.offer, quantity)
    validation.check_stock_is_bookable(stock)

    booking = BookingSQLEntity(
        recommendation=recommendation,
        stock=stock,
        quantity=quantity,
        token=random_token(),
        user=beneficiary,
        amount=stock.price,
    )

    expenses = get_user_expenses(beneficiary)
    validation.check_expenses_limits(expenses, booking)

    db.session.add(booking)

    notifier = MailjetNotificationService()
    notifier.send_booking_recap(booking)
    notifier.send_booking_confirmation_to_beneficiary(booking)

    return booking


def cancel_booking(user: UserSQLEntity, booking: BookingSQLEntity) -> None:
    validation.check_can_cancel_booking()

    booking.isCancelled = True

    notifier = MailjetNotificationService()
    notifier.send_booking_cancellation_emails_to_user_and_offerer(
        booking=booking,
        is_offerer_cancellation=False,
        is_user_cancellation=True,
        # FIXME: we should not have to pass this argument.
        # Notification-related code should be reorganized.
        send_email=send_raw_email,
    )

    if feature_queries.is_active(FeatureToggle.SYNCHRONIZE_ALGOLIA):
        redis.add_offer_id(client=app.redis_client, offer_id=booking.stock.offer.id)


# FIXME: not sure it's the right place...
def get_user_expenses(self, user: UserSQLEntity) -> dict:
    bookings = (
        BookingSQLEntity.query
        .filter_by(user=user)
        .filter_by(isCancelled=False)
        .options(
            joinedload(BookingSQLEntity.stock).
            joinedload(StockSQLEntity.offer)
        )
        .all()
    )
    return domain.expenses.get_expenses(bookings)
