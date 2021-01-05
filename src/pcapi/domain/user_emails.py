from datetime import datetime
from typing import Callable
from typing import List

from pcapi import settings
from pcapi.core.bookings.models import Booking
from pcapi.core.bookings.models import BookingCancellationReasons
from pcapi.core.users import models as users_models
from pcapi.core.users.models import UserSQLEntity
from pcapi.domain.beneficiary_pre_subscription.beneficiary_pre_subscription import BeneficiaryPreSubscription
from pcapi.emails import beneficiary_activation
from pcapi.emails.beneficiary_booking_cancellation import make_beneficiary_booking_cancellation_email_data
from pcapi.emails.beneficiary_booking_confirmation import retrieve_data_for_beneficiary_booking_confirmation_email
from pcapi.emails.beneficiary_expired_bookings import build_expired_bookings_recap_email_data_for_beneficiary
from pcapi.emails.beneficiary_offer_cancellation import (
    retrieve_offerer_booking_recap_email_data_after_user_cancellation,
)
from pcapi.emails.beneficiary_pre_subscription_rejected import (
    make_not_eligible_beneficiary_pre_subscription_rejected_data,
)
from pcapi.emails.beneficiary_pre_subscription_rejected import make_duplicate_beneficiary_pre_subscription_rejected_data
from pcapi.emails.beneficiary_soon_to_be_expired_bookings import (
    build_soon_to_be_expired_bookings_recap_email_data_for_beneficiary,
)
from pcapi.emails.beneficiary_warning_after_pro_booking_cancellation import (
    retrieve_data_to_warn_beneficiary_after_pro_booking_cancellation,
)
from pcapi.emails.new_offerer_validation import retrieve_data_for_new_offerer_validation_email
from pcapi.emails.offerer_attachment_validation import retrieve_data_for_offerer_attachment_validation_email
from pcapi.emails.offerer_booking_recap import retrieve_data_for_offerer_booking_recap_email
from pcapi.emails.offerer_bookings_recap_after_deleting_stock import (
    retrieve_offerer_bookings_recap_email_data_after_offerer_cancellation,
)
from pcapi.emails.offerer_expired_bookings import build_expired_bookings_recap_email_data_for_offerer
from pcapi.emails.offerer_ongoing_attachment import retrieve_data_for_offerer_ongoing_attachment_email
from pcapi.emails.pro_reset_password import retrieve_data_for_reset_password_pro_email
from pcapi.emails.pro_waiting_validation import retrieve_data_for_pro_user_waiting_offerer_validation_email
from pcapi.emails.user_notification_after_stock_update import (
    retrieve_data_to_warn_user_after_stock_update_affecting_booking,
)
from pcapi.emails.user_reset_password import retrieve_data_for_reset_password_native_app_email
from pcapi.emails.user_reset_password import retrieve_data_for_reset_password_user_email
from pcapi.models import Offerer
from pcapi.models import UserOfferer
from pcapi.utils.mailing import compute_email_html_part_and_recipients
from pcapi.utils.mailing import make_offerer_driven_cancellation_email_for_offerer
from pcapi.utils.mailing import make_user_validation_email


def send_booking_recap_emails(booking: Booking, send_email: Callable[..., bool]) -> None:
    recipients = [settings.ADMINISTRATION_EMAIL_ADDRESS]
    booking_email = booking.stock.offer.bookingEmail
    if booking_email:
        recipients.append(booking_email)

    data = retrieve_data_for_offerer_booking_recap_email(booking, recipients)
    send_email(data=data)


def send_booking_confirmation_email_to_beneficiary(booking: Booking, send_email: Callable[..., bool]) -> None:
    data = retrieve_data_for_beneficiary_booking_confirmation_email(booking)
    send_email(data=data)


def send_beneficiary_booking_cancellation_email(booking: Booking, send_email: Callable[..., bool]) -> None:
    data = make_beneficiary_booking_cancellation_email_data(booking)
    send_email(data=data)


def send_user_driven_cancellation_email_to_offerer(booking: Booking, send_email: Callable[..., bool]) -> None:
    recipients = _build_recipients_list(booking)
    data = retrieve_offerer_booking_recap_email_data_after_user_cancellation(booking, recipients)
    send_email(data=data)


def send_offerer_driven_cancellation_email_to_offerer(booking: Booking, send_email: Callable[..., bool]) -> None:
    offerer_email = booking.stock.offer.bookingEmail
    recipients = []
    if offerer_email:
        recipients.append(offerer_email)
    recipients.append(settings.ADMINISTRATION_EMAIL_ADDRESS)
    email = make_offerer_driven_cancellation_email_for_offerer(booking)
    email["Html-part"], email["To"] = compute_email_html_part_and_recipients(email["Html-part"], recipients)
    send_email(data=email)


def send_warning_to_beneficiary_after_pro_booking_cancellation(
    booking: Booking, send_email: Callable[..., bool]
) -> None:
    data = retrieve_data_to_warn_beneficiary_after_pro_booking_cancellation(booking)
    send_email(data=data)


def send_reset_password_email_to_user(user: UserSQLEntity, send_email: Callable[..., bool]) -> bool:
    data = retrieve_data_for_reset_password_user_email(user)
    return send_email(data=data)


def send_reset_password_email_to_native_app_user(
    user_email: str,
    token_value: str,
    expiration_date: datetime,
    send_email: Callable[..., bool],
) -> bool:
    data = retrieve_data_for_reset_password_native_app_email(user_email, token_value, expiration_date)
    return send_email(data=data)


def send_reset_password_email_to_pro(user: UserSQLEntity, send_email: Callable[..., bool]) -> None:
    data = retrieve_data_for_reset_password_pro_email(user)
    send_email(data=data)


def send_validation_confirmation_email_to_pro(offerer: Offerer, send_email: Callable[..., bool]) -> None:
    data = retrieve_data_for_new_offerer_validation_email(offerer)
    send_email(data=data)


def send_ongoing_offerer_attachment_information_email_to_pro(
    user_offerer: UserOfferer, send_email: Callable[..., bool]
) -> None:
    data = retrieve_data_for_offerer_ongoing_attachment_email(user_offerer)
    send_email(data=data)


def send_attachment_validation_email_to_pro_offerer(user_offerer: UserOfferer, send_email: Callable[..., bool]) -> None:
    data = retrieve_data_for_offerer_attachment_validation_email(user_offerer=user_offerer)
    send_email(data=data)


def send_batch_cancellation_emails_to_users(bookings: List[Booking], send_email: Callable[..., bool]) -> None:
    for booking in bookings:
        send_warning_to_beneficiary_after_pro_booking_cancellation(booking, send_email)


def send_offerer_bookings_recap_email_after_offerer_cancellation(
    bookings: List[Booking], send_email: Callable[..., bool]
) -> None:
    recipients = _build_recipients_list(bookings[0])
    data = retrieve_offerer_bookings_recap_email_data_after_offerer_cancellation(bookings, recipients)
    send_email(data=data)


def send_booking_cancellation_emails_to_user_and_offerer(
    booking: Booking, reason: BookingCancellationReasons, send_email: Callable[..., bool]
) -> None:
    if reason == BookingCancellationReasons.BENEFICIARY:
        send_beneficiary_booking_cancellation_email(booking, send_email)
        send_user_driven_cancellation_email_to_offerer(booking, send_email)
    if reason == BookingCancellationReasons.OFFERER:
        send_warning_to_beneficiary_after_pro_booking_cancellation(booking, send_email)
        send_offerer_driven_cancellation_email_to_offerer(booking, send_email)


def send_expired_bookings_recap_email_to_beneficiary(
    beneficiary: UserSQLEntity, bookings: List[Booking], send_email: Callable[..., bool]
) -> None:
    data = build_expired_bookings_recap_email_data_for_beneficiary(beneficiary, bookings)
    send_email(data=data)


def send_expired_bookings_recap_email_to_offerer(
    offerer: Offerer, bookings: List[Booking], send_email: Callable[..., bool]
) -> None:
    recipients = _build_recipients_list(bookings[0])
    data = build_expired_bookings_recap_email_data_for_offerer(offerer, recipients, bookings)
    send_email(data=data)


def send_user_validation_email(
    user: UserSQLEntity, send_email: Callable[..., bool], app_origin_url: str, is_webapp: bool
) -> None:
    data = make_user_validation_email(user, app_origin_url, is_webapp)
    send_email(data=data)


def send_pro_user_waiting_for_validation_by_admin_email(
    user: UserSQLEntity, send_email: Callable[..., bool], offerer: Offerer
) -> None:
    data = retrieve_data_for_pro_user_waiting_offerer_validation_email(user, offerer)
    send_email(data=data)


def send_soon_to_be_expired_bookings_recap_email_to_beneficiary(
    beneficiary: UserSQLEntity, bookings: List[Booking], send_email: Callable[..., bool]
) -> None:
    data = build_soon_to_be_expired_bookings_recap_email_data_for_beneficiary(beneficiary, bookings)
    send_email(data=data)


def send_activation_email(
    user: UserSQLEntity,
    send_email: Callable[..., bool],
    native_version: bool = False,
    token: users_models.Token = None,
) -> bool:
    if not native_version:
        data = beneficiary_activation.get_activation_email_data(user=user)
    else:
        data = beneficiary_activation.get_activation_email_data_for_native(user=user, token=token)
    return send_email(data=data)


def send_batch_stock_postponement_emails_to_users(bookings: List[Booking], send_email: Callable[..., bool]) -> None:
    for booking in bookings:
        send_booking_postponement_emails_to_users(booking, send_email)


def send_booking_postponement_emails_to_users(booking: Booking, send_email: Callable[..., bool]) -> None:
    data = retrieve_data_to_warn_user_after_stock_update_affecting_booking(booking)
    send_email(data=data)


def send_rejection_email_to_beneficiary_pre_subscription(
    beneficiary_pre_subscription: BeneficiaryPreSubscription,
    beneficiary_is_eligible: bool,
    send_email: Callable[..., bool],
) -> None:
    if not beneficiary_is_eligible:
        data = make_not_eligible_beneficiary_pre_subscription_rejected_data(beneficiary_pre_subscription.email)
    else:
        data = make_duplicate_beneficiary_pre_subscription_rejected_data(beneficiary_pre_subscription.email)
    send_email(data=data)


def _build_recipients_list(booking: Booking) -> str:
    recipients = []
    offerer_booking_email = booking.stock.offer.bookingEmail
    if offerer_booking_email:
        recipients.append(offerer_booking_email)
    recipients.append(settings.ADMINISTRATION_EMAIL_ADDRESS)
    return ", ".join(recipients)
