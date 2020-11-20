from typing import Dict

from pcapi import settings
from pcapi.models import Booking
from pcapi.utils.date import get_date_formatted_for_email
from pcapi.utils.date import get_time_formatted_for_email
from pcapi.utils.date import utc_datetime_to_department_timezone
from pcapi.utils.human_ids import humanize
from pcapi.utils.mailing import format_environment_for_email


def make_beneficiary_booking_cancellation_email_data(booking: Booking) -> Dict:
    stock = booking.stock
    beneficiary = booking.user
    offer = stock.offer
    beneficiary_email = beneficiary.email
    environment = format_environment_for_email()
    event_date = ""
    event_hour = ""
    first_name = beneficiary.firstName
    is_event = int(offer.isEvent)
    offer_id = humanize(offer.id)
    offer_name = offer.name
    price = str(stock.price * booking.quantity)
    is_free_offer = 1 if stock.price == 0 else 0
    mediation_id = humanize(booking.mediationId) if booking.mediationId is not None else "vide"

    if is_event:
        beginning_date_time_in_tz = utc_datetime_to_department_timezone(
            stock.beginningDatetime, offer.venue.departementCode
        )
        event_date = get_date_formatted_for_email(beginning_date_time_in_tz)
        event_hour = get_time_formatted_for_email(beginning_date_time_in_tz)

    return {
        "FromEmail": settings.SUPPORT_EMAIL_ADDRESS,
        "Mj-TemplateID": 1091464,
        "Mj-TemplateLanguage": True,
        "To": beneficiary_email,
        "Vars": {
            "env": environment,
            "event_date": event_date,
            "event_hour": event_hour,
            "is_free_offer": is_free_offer,
            "is_event": is_event,
            "mediation_id": mediation_id,
            "offer_id": offer_id,
            "offer_name": offer_name,
            "offer_price": price,
            "user_first_name": first_name,
        },
    }
