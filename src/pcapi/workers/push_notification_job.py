import logging
from typing import Any

from rq.decorators import job

from pcapi.core.users.models import User
from pcapi.notifications.push import send_transactional_notification
from pcapi.notifications.push import update_user_attributes
from pcapi.notifications.push.transactional_notifications import get_bookings_cancellation_notification_data
from pcapi.notifications.push.transactional_notifications import get_tomorrow_stock_notification_data
from pcapi.notifications.push.user_attributes_updates import get_user_attributes
from pcapi.workers import worker
from pcapi.workers.decorators import job_context
from pcapi.workers.decorators import log_job


logger = logging.getLogger(__name__)


@job(worker.default_queue, connection=worker.conn)
@job_context
@log_job
def update_user_attributes_job(user_id: int, **extra_data: Any) -> None:
    user = User.query.get(user_id)
    if not user:
        logger.error("No user with id=%s found to send push attributes updates requests", user_id)
        return

    attributes = get_user_attributes(user)
    attributes.update(extra_data)

    update_user_attributes(user.id, attributes)


@job(worker.default_queue, connection=worker.conn)
@job_context
@log_job
def send_cancel_booking_notification(bookings_ids: list[int]) -> None:
    notification_data = get_bookings_cancellation_notification_data(bookings_ids)
    if notification_data:
        send_transactional_notification(notification_data)


@job(worker.default_queue, connection=worker.conn)
@job_context
@log_job
def send_tomorrow_stock_notification(stock_id: int) -> None:
    notification_data = get_tomorrow_stock_notification_data(stock_id)
    if notification_data:
        send_transactional_notification(notification_data)
