from flask import current_app as app

from connectors import redis
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

from . import repository
from . import validation


def book_offer(
    beneficiary_id: int,
    stock_id: int,
    quantity: int,
    recommendation_id: int,
) -> BookingSQLEntity:
    """Return a booking or raise an exception if it's not possible."""
    beneficiary = users_repository.get_user_by_id(user_id)
    stock = repository.get_stock_by_id(stock_id)
    recommendation = recommendations_repository.get_recommendation_by_id(recommendation_id)

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

    expenses = repository.get_user_expenses(beneficiary)
    validation.check_expenses_limits(expenses, booking)

    db.session.add(booking)

    notifier = MailjetNotificationService()
    notifier.send_booking_recap(booking)
    notifier.send_booking_confirmation_to_beneficiary(booking)

    return booking


def cancel_booking(user_id: int, booking_id: int) -> None:
    user = users_repository.get_user_by_id(user_id)
    booking = repository.get_booking_by_id(booking_id)

    validation.check_can_cancel_booking(user, booking)

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

    return booking
