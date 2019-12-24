from typing import Callable, List

from emails.beneficiary_activation import get_activation_email_data
from emails.beneficiary_booking_cancellation import make_beneficiary_booking_cancellation_email_data
from emails.beneficiary_booking_confirmation import \
    retrieve_data_for_beneficiary_booking_confirmation_email
from emails.beneficiary_offer_cancellation import \
    retrieve_offerer_booking_recap_email_data_after_user_cancellation
from emails.beneficiary_warning_after_pro_booking_cancellation import \
    retrieve_data_to_warn_beneficiary_after_pro_booking_cancellation
from emails.new_offerer_validation import retrieve_data_for_new_offerer_validation_email
from emails.offerer_booking_recap import retrieve_data_for_offerer_booking_recap_email
from emails.offerer_bookings_recap_after_deleting_stock import \
    retrieve_offerer_bookings_recap_email_data_after_offerer_cancellation
from emails.pro_waiting_validation import retrieve_data_for_pro_user_waiting_offerer_validation_email
from emails.user_reset_password import retrieve_data_for_reset_password_email
from models import Booking, Offerer, Stock, User, Venue
from repository import booking_queries
from repository.stock_queries import set_booking_recap_sent_and_save
from repository.user_queries import find_all_emails_of_user_offerers_admins
from utils.logger import logger
from utils.mailing import ADMINISTRATION_EMAIL_ADDRESS, \
    compute_email_html_part_and_recipients, \
    make_reset_password_email, \
 \
    from utils.mailing import make_offerer_driven_cancellation_email_for_offerer, \
        make_final_recap_email_for_stock_with_event, \
        make_user_validation_email, \
        make_venue_validated_email


def send_final_booking_recap_email(stock: Stock, send_email: Callable[..., bool]) -> bool:
    stock_bookings = booking_queries.find_ongoing_bookings_by_stock(stock)
    if len(stock_bookings) == 0:
        logger.info("Not sending recap for  " + str(stock) + " as it has no bookings")
    email = make_final_recap_email_for_stock_with_event(stock)

    recipients = [ADMINISTRATION_EMAIL_ADDRESS]
    if stock.resolvedOffer.bookingEmail:
        recipients.append(stock.resolvedOffer.bookingEmail)

    email['Html-part'], email['To'] = compute_email_html_part_and_recipients(email['Html-part'], recipients)

    successfully_sent = send_email(data=email)

    set_booking_recap_sent_and_save(stock)
    return successfully_sent


def send_booking_recap_emails(booking: Booking, send_email: Callable[..., bool]) -> bool:
    recipients = [ADMINISTRATION_EMAIL_ADDRESS]
    if booking.stock.resolvedOffer.bookingEmail:
        recipients.append(booking.stock.resolvedOffer.bookingEmail)

    email = retrieve_data_for_offerer_booking_recap_email(booking, recipients)
    return send_email(data=email)


def send_booking_confirmation_email_to_beneficiary(booking: Booking, send_email: Callable[..., bool]):
    email_data = retrieve_data_for_beneficiary_booking_confirmation_email(booking)
    send_email(data=email_data)


def send_beneficiary_booking_cancellation_email(booking: Booking, send_email: Callable[..., bool]):
    beneficiary_booking_cancellation_email_data = make_beneficiary_booking_cancellation_email_data(booking)

    send_email(data=beneficiary_booking_cancellation_email_data)


def send_user_driven_cancellation_email_to_offerer(booking: Booking, send_email: Callable[..., bool]) -> bool:
    recipients = build_recipients_list(booking)
    mailjet_data = retrieve_offerer_booking_recap_email_data_after_user_cancellation(booking, recipients)
    return send_email(data=mailjet_data)


def send_warning_to_beneficiary_after_pro_booking_cancellation(booking: Booking,
                                                               send_email: Callable[..., bool]) -> None:
    email = retrieve_data_to_warn_beneficiary_after_pro_booking_cancellation(booking)
    send_email(data=email)


def send_offerer_driven_cancellation_email_to_offerer(booking: Booking, send_email: Callable[..., bool]) -> bool:
    offerer_email = booking.stock.resolvedOffer.bookingEmail
    recipients = []
    if offerer_email:
        recipients.append(offerer_email)
    recipients.append(ADMINISTRATION_EMAIL_ADDRESS)
    email = make_offerer_driven_cancellation_email_for_offerer(booking)
    email['Html-part'], email['To'] = compute_email_html_part_and_recipients(email['Html-part'], recipients)
    return send_email(data=email)


def send_reset_password_email(user: User, send_email: Callable[..., bool], app_origin_url: str) -> bool:
    email = make_reset_password_email(user, app_origin_url)
    recipients = [user.email]
    email['Html-part'], email['To'] = compute_email_html_part_and_recipients(email['Html-part'], recipients)
    return send_email(data=email)


def send_reset_password_email_with_mailjet_template(user: User, send_email: Callable[..., bool]) -> bool:
    email = retrieve_data_for_reset_password_email(user)
    return send_email(data=email)


def send_validation_confirmation_email_to_pro(offerer: Offerer, send_email: Callable[..., bool]) -> None:
    email = retrieve_data_for_new_offerer_validation_email(offerer)
    send_email(data=email)


def send_batch_cancellation_emails_to_users(bookings: List[Booking], send_email: Callable[..., bool]) -> None:
    for booking in bookings:
        send_warning_to_beneficiary_after_pro_booking_cancellation(booking, send_email)


def send_batch_cancellation_email_to_offerer(bookings: List[Booking], send_email: Callable[..., bool]) -> bool:
    booking = bookings[0]
    recipients = build_recipients_list(booking)
    email = retrieve_offerer_bookings_recap_email_data_after_offerer_cancellation(bookings, recipients)
    return send_email(data=email)


def send_cancellation_emails_to_user_and_offerer(booking: Booking, is_offerer_cancellation: bool,
                                                 is_user_cancellation: bool, send_email: Callable[..., bool]):
    if is_user_cancellation:
        send_beneficiary_booking_cancellation_email(booking, send_email)
        send_user_driven_cancellation_email_to_offerer(booking, send_email)
    if is_offerer_cancellation:
        send_warning_to_beneficiary_after_pro_booking_cancellation(booking, send_email)
        send_offerer_driven_cancellation_email_to_offerer(booking, send_email)


def send_venue_validation_confirmation_email(venue: Venue, send_email: Callable[..., bool]) -> bool:
    recipients = find_all_emails_of_user_offerers_admins(venue.managingOffererId)
    email = make_venue_validated_email(venue)
    email['Html-part'], email['To'] = compute_email_html_part_and_recipients(email['Html-part'], recipients)
    return send_email(data=email)


def send_user_validation_email(user: User, send_email: Callable[..., bool], app_origin_url: str, is_webapp) -> bool:
    email = make_user_validation_email(user, app_origin_url, is_webapp)
    return send_email(data=email)


def send_pro_user_waiting_for_validation_by_admin_email(user: User, send_email: Callable[..., bool],
                                                        offerer: Offerer) -> bool:
    email = retrieve_data_for_pro_user_waiting_offerer_validation_email(user, offerer)
    return send_email(data=email)


def send_activation_email(user: User, send_email: Callable[..., bool]) -> bool:
    activation_email_data = get_activation_email_data(user)

    return send_email(activation_email_data)


def build_recipients_list(booking: Booking) -> str:
    recipients = []
    offerer_booking_email = booking.stock.resolvedOffer.bookingEmail
    if offerer_booking_email:
        recipients.append(offerer_booking_email)
    recipients.append(ADMINISTRATION_EMAIL_ADDRESS)
    return ", ".join(recipients)
