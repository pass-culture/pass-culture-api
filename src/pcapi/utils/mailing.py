import base64
from datetime import datetime
import io
from pprint import pformat
from typing import Dict
from typing import List
from typing import Union
import zipfile

from flask import current_app as app
from flask import render_template
from requests import Response

from pcapi import settings
from pcapi.connectors import api_entreprises
from pcapi.core.bookings.repository import find_ongoing_bookings_by_stock
from pcapi.core.users.models import User
from pcapi.domain.postal_code.postal_code import PostalCode
from pcapi.models import Booking
from pcapi.models import Offer
from pcapi.models import Offerer
from pcapi.models import Stock
from pcapi.models import UserOfferer
from pcapi.models.email import EmailStatus
from pcapi.repository.email_queries import save
from pcapi.repository.feature_queries import feature_send_mail_to_users_enabled
from pcapi.utils import logger
from pcapi.utils.date import format_datetime
from pcapi.utils.date import utc_datetime_to_department_timezone
from pcapi.utils.human_ids import humanize


class MailServiceException(Exception):
    pass


def send_raw_email(data: Dict) -> bool:
    successfully_sent_email = False
    try:
        if settings.SEND_RAW_EMAIL_BACKEND == "log":
            logger.logger.info("[EMAIL] Sending email %s", data)
            successfully_sent_email = True
        else:
            if settings.MAILJET_TEMPLATE_DEBUGGING:
                messages_data = data.get("Messages")
                if messages_data:
                    for message_data in messages_data:
                        _add_template_debugging(message_data)
                else:
                    _add_template_debugging(data)
            response = app.mailjet_client.send.create(data=data)
            successfully_sent_email = response.status_code == 200
        status = EmailStatus.SENT if successfully_sent_email else EmailStatus.ERROR
        save(data, status)
        if not successfully_sent_email:
            logger.logger.warning("[EMAIL] Trying to send email failed with status code %s", response.status_code)
    except Exception as exc:  # pylint: disable=broad-except
        logger.logger.exception("[EMAIL] Trying to send email failed with unexpected error %s", exc)

    return successfully_sent_email


def create_contact(email: str) -> Response:
    data = {"Email": email}

    return app.mailjet_client.contact.create(data=data)


def add_contact_informations(email: str, date_of_birth: str, department_code: str) -> Response:
    data = {
        "Data": [
            {"Name": "date_de_naissance", "Value": date_of_birth},
            {"Name": "département", "Value": department_code},
        ]
    }

    return app.mailjet_client.contactdata.update(id=email, data=data)


def add_contact_to_list(email: str, list_id: str) -> Response:
    data = {
        "IsUnsubscribed": "false",
        "ContactAlt": email,
        "ListID": list_id,
    }

    return app.mailjet_client.listrecipient.create(data=data)


def build_pc_pro_offer_link(offer: Offer) -> str:
    return (
        f"{settings.PRO_URL}/offres/{humanize(offer.id)}?lieu={humanize(offer.venueId)}"
        f"&structure={humanize(offer.venue.managingOffererId)}"
    )


def extract_users_information_from_bookings(bookings: List[Booking]) -> List[dict]:
    users_keys = ("firstName", "lastName", "email", "contremarque")
    users_properties = [
        [booking.user.firstName, booking.user.lastName, booking.user.email, booking.token] for booking in bookings
    ]

    return [dict(zip(users_keys, user_property)) for user_property in users_properties]


def create_email_recipients(recipients: List[str]) -> str:
    if feature_send_mail_to_users_enabled():
        return ", ".join(recipients)
    return settings.DEV_EMAIL_ADDRESS


def format_environment_for_email() -> str:
    return "" if settings.IS_PROD else f"-{settings.ENV}"


def format_booking_date_for_email(booking: Booking) -> str:
    if booking.stock.offer.isEvent:
        date_in_tz = get_event_datetime(booking.stock)
        offer_date = date_in_tz.strftime("%d-%b-%Y")
        return offer_date
    return ""


def format_booking_hours_for_email(booking: Booking) -> str:
    if booking.stock.offer.isEvent:
        date_in_tz = get_event_datetime(booking.stock)
        event_hour = date_in_tz.hour
        event_minute = date_in_tz.minute
        return f"{event_hour}h" if event_minute == 0 else f"{event_hour}h{event_minute}"
    return ""


def make_validation_email_object(
    offerer: Offerer, user_offerer: UserOfferer, get_by_siren=api_entreprises.get_by_offerer
) -> Dict:
    vars_obj_user = vars(user_offerer.user)
    vars_obj_user.pop("clearTextPassword", None)
    api_entreprise = get_by_siren(offerer)

    offerer_departement_code = PostalCode(offerer.postalCode).get_departement_code()

    email_html = render_template(
        "mails/internal_validation_email.html",
        user_offerer=user_offerer,
        user_vars=pformat(vars_obj_user),
        offerer=offerer,
        offerer_vars_user_offerer=pformat(vars(user_offerer.offerer)),
        offerer_vars=pformat(vars(offerer)),
        api_entreprise=pformat(api_entreprise),
        api_url=settings.API_URL,
    )

    return {
        "FromName": "pass Culture",
        "FromEmail": settings.SUPPORT_EMAIL_ADDRESS,
        "Subject": "%s - inscription / rattachement PRO à valider : %s" % (offerer_departement_code, offerer.name),
        "Html-part": email_html,
    }


def make_offerer_driven_cancellation_email_for_offerer(booking: Booking) -> Dict:
    stock_name = booking.stock.offer.name
    venue = booking.stock.offer.venue
    user_name = booking.user.publicName
    user_email = booking.user.email
    email_subject = "Confirmation de votre annulation de réservation pour {}, proposé par {}".format(
        stock_name, venue.name
    )
    ongoing_stock_bookings = find_ongoing_bookings_by_stock(booking.stock.id)
    stock_date_time = None
    booking_is_on_event = booking.stock.beginningDatetime is not None
    if booking_is_on_event:
        date_in_tz = get_event_datetime(booking.stock)
        stock_date_time = format_datetime(date_in_tz)
    email_html = render_template(
        "mails/offerer_recap_email_after_offerer_cancellation.html",
        booking_is_on_event=booking_is_on_event,
        user_name=user_name,
        user_email=user_email,
        stock_date_time=stock_date_time,
        number_of_bookings=len(ongoing_stock_bookings),
        stock_bookings=ongoing_stock_bookings,
        stock_name=stock_name,
        venue=venue,
    )
    return {
        "FromName": "pass Culture",
        "FromEmail": settings.SUPPORT_EMAIL_ADDRESS
        if feature_send_mail_to_users_enabled()
        else settings.DEV_EMAIL_ADDRESS,
        "Subject": email_subject,
        "Html-part": email_html,
    }


def make_user_validation_email(user: User, app_origin_url: str, is_webapp: bool) -> Dict:
    if is_webapp:
        data = make_webapp_user_validation_email(user, app_origin_url)
    else:
        data = make_pro_user_validation_email(user, app_origin_url)
    return data


def get_contact(user: User) -> Union[str, None]:
    mailjet_json_response = app.mailjet_client.contact.get(user.email).json()
    return mailjet_json_response["Data"][0] if "Data" in mailjet_json_response else None


def subscribe_newsletter(user: User):
    if not feature_send_mail_to_users_enabled():
        logger.logger.info("Subscription in DEV or STAGING mode is disabled")
        return None

    try:
        contact = get_contact(user)
    except Exception:  # pylint: disable=broad-except
        contact_data = {"Email": user.email, "Name": user.publicName}
        contact_json = app.mailjet_client.contact.create(data=contact_data).json()
        contact = contact_json["Data"][0] if "Data" in contact_json else None

    if contact is None:
        raise MailServiceException

    # ('Pass Culture - Liste de diffusion', 1795144)
    contact_lists_data = {"ContactsLists": [{"Action": "addnoforce", "ListID": 1795144}]}

    return app.mailjet_client.contact_managecontactslists.create(id=contact["ID"], data=contact_lists_data).json()


def make_payment_message_email(xml: str, checksum: bytes) -> Dict:
    now = datetime.utcnow()
    xml_b64encode = base64.b64encode(xml.encode("utf-8")).decode()
    file_name = "message_banque_de_france_{}.xml".format(datetime.strftime(now, "%Y%m%d"))

    return {
        "FromEmail": settings.SUPPORT_EMAIL_ADDRESS,
        "FromName": "pass Culture Pro",
        "Subject": "Virements XML pass Culture Pro - {}".format(datetime.strftime(now, "%Y-%m-%d")),
        "Attachments": [{"ContentType": "text/xml", "Filename": file_name, "Content": xml_b64encode}],
        "Html-part": render_template("mails/payments_xml_email.html", file_name=file_name, file_hash=checksum.hex()),
    }


def _get_zipfile_content(content: str, filename: str):
    """Return the content of a ZIP fie that would include a single file
    with the requested content and filename.
    """
    stream = io.BytesIO()
    zf = zipfile.ZipFile(stream, mode="w", compression=zipfile.ZIP_DEFLATED, compresslevel=9)
    zf.writestr(filename, content)
    zf.close()
    stream.seek(0)
    return stream.read()


def make_payment_details_email(csv: str) -> Dict:
    now = datetime.utcnow()
    csv_filename = f"details_des_paiements_{datetime.strftime(now, '%Y%m%d')}.csv"
    zipfile_content = _get_zipfile_content(csv, csv_filename)
    return {
        "FromEmail": settings.SUPPORT_EMAIL_ADDRESS,
        "FromName": "pass Culture Pro",
        "Subject": "Détails des paiements pass Culture Pro - {}".format(datetime.strftime(now, "%Y-%m-%d")),
        "Attachments": [
            {
                "ContentType": "application/zip",
                "Filename": f"{csv_filename}.zip",
                "Content": base64.b64encode(zipfile_content).decode(),
            },
        ],
        "Html-part": "",
    }


def make_payments_report_email(not_processable_csv: str, error_csv: str, grouped_payments: Dict) -> Dict:
    now = datetime.utcnow()
    not_processable_csv_b64encode = base64.b64encode(not_processable_csv.encode("utf-8")).decode()
    error_csv_b64encode = base64.b64encode(error_csv.encode("utf-8")).decode()
    formatted_date = datetime.strftime(now, "%Y-%m-%d")

    def number_of_payments_for_one_status(key_value):
        return len(key_value[1])

    total_number_of_payments = sum(map(number_of_payments_for_one_status, grouped_payments.items()))

    return {
        "Subject": "Récapitulatif des paiements pass Culture Pro - {}".format(formatted_date),
        "FromEmail": settings.SUPPORT_EMAIL_ADDRESS,
        "FromName": "pass Culture Pro",
        "Attachments": [
            {
                "ContentType": "text/csv",
                "Filename": "paiements_non_traitables_{}.csv".format(formatted_date),
                "Content": not_processable_csv_b64encode,
            },
            {
                "ContentType": "text/csv",
                "Filename": "paiements_en_erreur_{}.csv".format(formatted_date),
                "Content": error_csv_b64encode,
            },
        ],
        "Html-part": render_template(
            "mails/payments_report_email.html",
            date_sent=formatted_date,
            total_number=total_number_of_payments,
            grouped_payments=grouped_payments,
        ),
    }


def make_wallet_balances_email(csv: str) -> Dict:
    now = datetime.utcnow()
    csv_b64encode = base64.b64encode(csv.encode("utf-8")).decode()
    return {
        "FromEmail": settings.SUPPORT_EMAIL_ADDRESS,
        "FromName": "pass Culture Pro",
        "Subject": "Soldes des utilisateurs pass Culture - {}".format(datetime.strftime(now, "%Y-%m-%d")),
        "Attachments": [
            {
                "ContentType": "text/csv",
                "Filename": "soldes_des_utilisateurs_{}.csv".format(datetime.strftime(now, "%Y%m%d")),
                "Content": csv_b64encode,
            }
        ],
        "Html-part": "",
    }


def compute_email_html_part_and_recipients(email_html_part, recipients: Union[List[str], str]) -> (str, str):
    if isinstance(recipients, list):
        recipients_string = ", ".join(recipients)
    else:
        recipients_string = recipients
    if feature_send_mail_to_users_enabled():
        email_to = recipients_string
    else:
        email_html_part = (
            "<p>This is a test (ENV={environment})."
            " In production, email would have been sent to : {recipients}</p>{html_part}".format(
                environment=settings.ENV, recipients=recipients_string, html_part=email_html_part
            )
        )
        email_to = settings.DEV_EMAIL_ADDRESS
    return email_html_part, email_to


def make_offer_creation_notification_email(offer: Offer, author: User) -> Dict:
    pro_link_to_offer = f"{settings.PRO_URL}/offres/{humanize(offer.id)}"
    webapp_link_to_offer = f"{settings.WEBAPP_URL}/offre/details/{humanize(offer.id)}"
    venue = offer.venue
    pro_venue_link = f"{settings.PRO_URL}/lieux/{humanize(venue.id)}"
    html = render_template(
        "mails/offer_creation_notification_email.html",
        offer=offer,
        venue=venue,
        author=author,
        pro_link_to_offer=pro_link_to_offer,
        webapp_link_to_offer=webapp_link_to_offer,
        pro_venue_link=pro_venue_link,
    )
    location_information = offer.venue.departementCode or "numérique"
    return {
        "Html-part": html,
        "To": [settings.ADMINISTRATION_EMAIL_ADDRESS],
        "FromEmail": settings.SUPPORT_EMAIL_ADDRESS,
        "FromName": "pass Culture",
        "Subject": f"[Création d’offre - {location_information}] {offer.product.name}",
    }


def get_event_datetime(stock: Stock) -> datetime:
    if stock.offer.venue.departementCode is not None:
        date_in_utc = stock.beginningDatetime
        date_in_tz = utc_datetime_to_department_timezone(date_in_utc, stock.offer.venue.departementCode)
    else:
        date_in_tz = stock.beginningDatetime

    return date_in_tz


def make_webapp_user_validation_email(user: User, app_origin_url: str) -> Dict:
    template = "mails/webapp_user_validation_email.html"
    email_html = render_template(template, user=user, api_url=settings.API_URL, app_origin_url=app_origin_url)
    return {
        "Html-part": email_html,
        "To": user.email,
        "Subject": "Validation de votre adresse email pour le pass Culture",
        "FromName": "pass Culture",
        "FromEmail": settings.SUPPORT_EMAIL_ADDRESS
        if feature_send_mail_to_users_enabled()
        else settings.DEV_EMAIL_ADDRESS,
    }


def make_pro_user_validation_email(user: User, app_origin_url: str) -> Dict:
    return {
        "FromEmail": settings.SUPPORT_EMAIL_ADDRESS
        if feature_send_mail_to_users_enabled()
        else settings.DEV_EMAIL_ADDRESS,
        "FromName": "pass Culture pro",
        "Subject": "[pass Culture pro] Validation de votre adresse email pour le pass Culture",
        "MJ-TemplateID": 778688,
        "MJ-TemplateLanguage": True,
        "Recipients": [{"Email": user.email, "Name": user.publicName}],
        "Vars": {
            "nom_structure": user.publicName,
            "lien_validation_mail": f"{app_origin_url}/inscription/validation/{user.validationToken}",
        },
    }


def _add_template_debugging(message_data: Dict) -> None:
    message_data["TemplateErrorReporting"] = {
        "Email": settings.DEV_EMAIL_ADDRESS,
        "Name": "Mailjet Template Errors",
    }
