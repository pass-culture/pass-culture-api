""" mailing """
import base64
import os
from datetime import datetime
from flask import current_app as app, render_template
from pprint import pformat
from typing import Dict, List

from connectors import api_entreprises
from domain.user_activation import generate_set_password_url
from models import Offer
from models import RightsType, User
from repository import email_failed_queries
from repository.booking_queries import find_all_ongoing_bookings_by_stock
from repository.features import feature_send_mail_to_users_enabled
from repository.user_offerer_queries import find_user_offerer_email
from utils import logger
from utils.config import API_URL, ENV, WEBAPP_URL, PRO_URL
from utils.date import format_datetime, utc_datetime_to_dept_timezone
from utils.human_ids import humanize

MAILJET_API_KEY = os.environ.get('MAILJET_API_KEY')
MAILJET_API_SECRET = os.environ.get('MAILJET_API_SECRET')
OBJECT_STORAGE_URL = os.environ.get('OBJECT_STORAGE_URL')

if MAILJET_API_KEY is None or MAILJET_API_KEY == '':
    raise ValueError("Missing environment variable MAILJET_API_KEY")

if MAILJET_API_SECRET is None or MAILJET_API_SECRET == '':
    raise ValueError("Missing environment variable MAILJET_API_SECRET")


class MailServiceException(Exception):
    pass


def email_was_sent_or_save_error(mail_result, email):
    if mail_result.status_code != 200:
        email_failed_queries.save(email)
        return False
    return True


def make_batch_cancellation_email(bookings, cancellation_case):
    booking = next(iter(bookings))
    offer_name = booking.stock.resolvedOffer.eventOrThing.name
    email_html = render_template('mails/offerer_batch_cancellation_email.html',
                                 offer_name=offer_name, bookings=bookings, cancellation_case=cancellation_case)
    email_subject = 'Annulation de réservations pour %s' % offer_name
    return {
        'FromName': 'pass Culture pro',
        'FromEmail': 'support.passculture@beta.gouv.fr',
        'Subject': email_subject,
        'Html-part': email_html,
    }


def make_final_recap_email_for_stock_with_event(stock):
    booking_is_on_event = stock.eventOccurrence is not None
    venue = stock.resolvedOffer.venue
    date_in_tz = _get_event_datetime(stock)
    formatted_datetime = format_datetime(date_in_tz)
    email_subject = '[Réservations] Récapitulatif pour {} le {}'.format(stock.eventOccurrence.offer.event.name,
                                                                        formatted_datetime)
    stock_bookings = find_all_ongoing_bookings_by_stock(stock)
    email_html = render_template('mails/offerer_final_recap_email.html',
                                 booking_is_on_event=booking_is_on_event,
                                 number_of_bookings=len(stock_bookings),
                                 stock_name=stock.eventOccurrence.offer.event.name,
                                 stock_date_time=formatted_datetime,
                                 venue=venue,
                                 stock_bookings=stock_bookings)

    return {
        'FromName': 'Pass Culture',
        'FromEmail': 'support.passculture@beta.gouv.fr',
        'Subject': email_subject,
        'Html-part': email_html,
    }


def make_offerer_booking_recap_email_after_user_action(booking, is_cancellation=False):
    venue = booking.stock.resolvedOffer.venue
    user = booking.user
    stock_bookings = find_all_ongoing_bookings_by_stock(booking.stock)
    event_or_thing = booking.stock.resolvedOffer.eventOrThing
    human_offer_id = humanize(booking.stock.resolvedOffer.id)
    booking_is_on_event = booking.stock.eventOccurrence is not None

    if is_cancellation:
        email_subject = f'[Réservations] Annulation de réservation pour {event_or_thing.name}'
    else:
        email_subject = f'[Réservations {venue.departementCode}] Nouvelle réservation pour {event_or_thing.name}'

    if booking_is_on_event:
        date_in_tz = _get_event_datetime(booking.stock)
        formatted_datetime = format_datetime(date_in_tz)
        email_subject += f' - {formatted_datetime}'
    else:
        formatted_datetime = None
    email_html = render_template('mails/offerer_recap_email_after_user_action.html',
                                 is_cancellation=is_cancellation,
                                 booking_is_on_event=booking_is_on_event,
                                 number_of_bookings=len(stock_bookings),
                                 event_or_thing=event_or_thing,
                                 stock_date_time=formatted_datetime,
                                 venue=venue,
                                 stock_bookings=stock_bookings,
                                 user=user,
                                 pro_url=PRO_URL,
                                 human_offer_id=human_offer_id)

    return {
        'FromName': 'Pass Culture',
        'FromEmail': 'support.passculture@beta.gouv.fr',
        'Subject': email_subject,
        'Html-part': email_html,
    }


def write_object_validation_email(offerer, user_offerer, get_by_siren=api_entreprises.get_by_siren):
    vars_obj_user = vars(user_offerer.user)
    vars_obj_user.pop('clearTextPassword', None)
    api_entreprise = get_by_siren(offerer).json()

    email_html = render_template('mails/internal_validation_email.html',
                                 user_offerer=user_offerer,
                                 user_vars=pformat(vars_obj_user),
                                 offerer=offerer,
                                 offerer_vars_user_offerer=pformat(vars(user_offerer.offerer)),
                                 offerer_vars=pformat(vars(offerer)),
                                 api_entreprise=pformat(api_entreprise),
                                 api_url=API_URL)

    return {
        'FromName': 'Pass Culture',
        'FromEmail': 'support.passculture@beta.gouv.fr',
        'Subject': "%s - inscription / rattachement PRO à valider : %s" % (
            user_offerer.user.departementCode, offerer.name),
        'Html-part': email_html
    }


def make_offerer_driven_cancellation_email_for_user(booking):
    offer_name = booking.stock.resolvedOffer.eventOrThing.name
    offerer_name = booking.stock.resolvedOffer.venue.managingOfferer.name
    booking_value = booking.amount * booking.quantity
    booking_is_on_event = booking.stock.eventOccurrence is not None
    formatted_datetime = None
    commande_ou_reservation = 'réservation' if booking_is_on_event else 'commande'
    if booking_is_on_event:
        date_in_tz = _get_event_datetime(booking.stock)
        formatted_datetime = format_datetime(date_in_tz)

    email_html = render_template('mails/user_cancellation_by_offerer_email.html',
                                 booking_is_on_event=booking_is_on_event,
                                 user=booking.user,
                                 offer_name=offer_name,
                                 event_date=formatted_datetime,
                                 offerer_name=offerer_name,
                                 booking_value=booking_value
                                 )

    email_subject = 'Votre {} pour {}, proposé par {} a été annulée par l\'offreur'.format(commande_ou_reservation,
                                                                                           offer_name, offerer_name)

    return {
        'FromName': 'Pass Culture',
        'FromEmail': 'support.passculture@beta.gouv.fr' if feature_send_mail_to_users_enabled() else 'passculture-dev@beta.gouv.fr',
        'Subject': email_subject,
        'Html-part': email_html,
    }


def make_offerer_driven_cancellation_email_for_offerer(booking):
    stock_name = booking.stock.resolvedOffer.eventOrThing.name
    venue = booking.stock.resolvedOffer.venue
    user_name = booking.user.publicName
    user_email = booking.user.email
    email_subject = 'Confirmation de votre annulation de réservation pour {}, proposé par {}'.format(stock_name,
                                                                                                     venue.name)
    ongoing_stock_bookings = find_all_ongoing_bookings_by_stock(booking.stock)
    stock_date_time = None
    booking_is_on_event = booking.stock.eventOccurrence is not None
    if booking_is_on_event:
        date_in_tz = _get_event_datetime(booking.stock)
        stock_date_time = format_datetime(date_in_tz)
    email_html = render_template('mails/offerer_recap_email_after_offerer_cancellation.html',
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
        'FromName': 'Pass Culture',
        'FromEmail': 'support.passculture@beta.gouv.fr' if feature_send_mail_to_users_enabled() else 'passculture-dev@beta.gouv.fr',
        'Subject': email_subject,
        'Html-part': email_html,
    }


def make_user_booking_recap_email(booking, is_cancellation=False):
    stock = booking.stock
    user = booking.user
    if is_cancellation:
        email_html, email_subject = _generate_user_driven_cancellation_email_for_user(user,
                                                                                      stock)
    else:
        email_html, email_subject = _generate_reservation_email_html_subject(booking)

    return {
        'FromName': 'Pass Culture',
        'FromEmail': 'support.passculture@beta.gouv.fr' if feature_send_mail_to_users_enabled() else 'passculture-dev@beta.gouv.fr',
        'Subject': email_subject,
        'Html-part': email_html,
    }


def make_reset_password_email(user, app_origin_url):
    email_html = render_template(
        'mails/user_reset_password_email.html',
        user=user,
        app_origin_url=app_origin_url
    )

    return {
        'FromName': 'Pass Culture',
        'FromEmail': 'support.passculture@beta.gouv.fr',
        'Subject': 'Réinitialisation de votre mot de passe',
        'Html-part': email_html,
    }


def make_validation_confirmation_email(user_offerer, offerer):
    user_offerer_email = None
    user_offerer_rights = None
    if user_offerer is not None:
        user_offerer_email = find_user_offerer_email(user_offerer.id)
        if user_offerer.rights == RightsType.admin:
            user_offerer_rights = 'administrateur'
        else:
            user_offerer_rights = 'éditeur'
    email_html = render_template(
        'mails/user_offerer_and_offerer_validation_confirmation_email.html',
        user_offerer_email=user_offerer_email,
        offerer=offerer,
        user_offerer_rights=user_offerer_rights
    )
    if user_offerer and offerer:
        subject = 'Validation de votre structure et de compte {} rattaché'.format(user_offerer_rights)
    elif user_offerer:
        subject = 'Validation de compte {} rattaché à votre structure'.format(user_offerer_rights)
    else:
        subject = 'Validation de votre structure'
    return {
        'FromName': 'pass Culture pro',
        'FromEmail': 'support.passculture@beta.gouv.fr' if feature_send_mail_to_users_enabled() else 'passculture-dev@beta.gouv.fr',
        'Subject': subject,
        'Html-part': email_html,
    }


def make_venue_validation_email(venue):
    html = render_template('mails/venue_validation_email.html', venue=venue, api_url=API_URL)
    return {
        'FromEmail': 'support.passculture@beta.gouv.fr',
        'FromName': 'pass Culture',
        'Subject': '{} - rattachement de lieu pro à valider : {}'.format(venue.departementCode, venue.name),
        'Html-part': html
    }


def make_activation_notification_email(user: User) -> dict:
    first_name = user.firstName.capitalize()
    set_password_url = generate_set_password_url(WEBAPP_URL, user)

    return {
        'FromEmail': 'support.passculture@beta.gouv.fr',
        'FromName': 'Équipe pass Culture',
        'Subject': 'Votre pass Culture est disponible',
        'Text-Part': _make_activation_notification_email_as_plain_text(first_name, set_password_url),
        'Html-part': render_template(
            'mails/activation_notification_email.html',
            first_name=first_name,
            set_password_link=set_password_url,
            object_storage_url=OBJECT_STORAGE_URL
        )
    }


def _make_activation_notification_email_as_plain_text(first_name: str, set_password_link: str) -> str:
    return f"""
    * Vous pouvez télécharger votre pass culture *


    Bonjour {first_name},

    Félicitations !
    Votre pass Culture est désormais activé et votre compte est crédité de 500 euros.

    Cliquez ici pour accéder à l'application :
    {set_password_link}

    ———

    Le pass Culture, c’est l’application qui vous permettra d’accéder à toutes les sorties ou pratiques culturelles près de chez vous.

    Spectacles, rencontres, visites particulières, abonnements cinéma… Soyez curieux !

    Explorez les nombreuses propositions sur l’application pour vous adonner à vos passions ou tenter de nouvelles expériences.

    Pour profiter au mieux de l’application sur smartphone, épinglez vous-même votre pass Culture à votre écran d’accueil ; tout est expliqué ici : https://pass.culture.fr/assets/docs/Tuto-app_passCulture-mobile.pdf

    ———

    Le pass Culture est dans sa phase d’expérimentation. Il est en construction permanente. Nous travaillons tous les jours à son amélioration. Mais vous pouvez aussi nous aider !

    ———

    * Le mot du ministre *    

    «Je vous remercie d’avoir répondu présents en si grand nombre pour prendre part à cette expérimentation sans précédent. Pour une fois, l’on ne vous dira pas que la curiosité est un vilain défaut. Je vous invite précisément à être curieux. Le pass Culture est une formidable chance d’explorer des domaines de la culture que vous ne connaissez pas encore, profitez-en. Faites-nous part également de tous vos retours, autant que possible, la période qui s’ouvre est faite pour cela. Nous avons le plaisir de construire ensemble le pass Culture dont des générations entières de jeunes de votre âge bénéficieront dans les années à venir. Gardez d’ailleurs en tête que la culture doit toujours rester associée au plaisir. Je vous souhaite donc de faire de belles découvertes sur le pass Culture et, surtout, de vous y amuser.»

    Franck Riester
    Ministre de la Culture

    ———

    * Écrivez-nous, nous sommes à votre écoute *

    On adore vous lire alors n’hésitez pas à nous dire…
    • ce que vous aimez,
    • ce que vous aimez moins,
    • si vous rencontrez un problème,
    • si vous souhaitez nous donner des idées sur les nouvelles fonctionnalités que
    vous aimeriez que le pass Culture vous propose !

    ———

    Bonnes découvertes et à très vite !



    L'équipe du pass Culture



    Facebook : https://facebook.com/passCultureofficiel
    Instagram : https://instagram.com/passCultureofficiel
    Snapchat : https://www.snapchat.com/add/pass.culture
    Twitter : https://twitter.com/pass_culture

    support.passculture@beta.gouv.fr • pass.culture.fr
    """


def make_user_validation_email(user, app_origin_url, is_webapp):
    if is_webapp:
        template = 'mails/webapp_user_validation_email.html'
        from_name = 'pass Culture'
    else:
        template = 'mails/pro_user_validation_email.html'
        from_name = 'pass Culture pro'
    email_html = render_template(template, user=user, api_url=API_URL, app_origin_url=app_origin_url)
    return {'Html-part': email_html,
            'To': user.email,
            'Subject': 'Validation de votre adresse email pour le pass Culture',
            'FromName': from_name,
            'FromEmail': 'support.passculture@beta.gouv.fr' if feature_send_mail_to_users_enabled() else 'passculture-dev@beta.gouv.fr'}


def get_contact(user):
    mailjet_json_response = app.mailjet_client.contact.get(user.email).json()
    return mailjet_json_response['Data'][0] if 'Data' in mailjet_json_response else None


def subscribe_newsletter(user):
    if not feature_send_mail_to_users_enabled():
        logger.logger.info("Subscription in DEV or STAGING mode is disabled")
        return

    try:
        contact = get_contact(user)
    except:
        contact_data = {
            'Email': user.email,
            'Name': user.publicName
        }
        contact_json = app.mailjet_client.contact.create(data=contact_data).json()
        contact = contact_json['Data'][0] if 'Data' in contact_json else None

    if contact is None:
        raise MailServiceException

    # ('Pass Culture - Liste de diffusion', 1795144)
    contact_lists_data = {
        "ContactsLists": [
            {
                "Action": "addnoforce",
                "ListID": 1795144
            }
        ]
    }

    return app.mailjet_client.contact_managecontactslists.create(
        id=contact['ID'],
        data=contact_lists_data
    ).json()


def make_payment_transaction_email(xml: str, checksum: bytes) -> dict:
    now = datetime.utcnow()
    xml_b64encode = base64.b64encode(xml.encode('utf-8')).decode()
    file_name = "transaction_banque_de_france_{}.xml".format(datetime.strftime(now, "%Y%m%d"))

    return {
        'FromEmail': 'support.passculture@beta.gouv.fr',
        'FromName': "pass Culture Pro",
        'Subject': "Virements XML pass Culture Pro - {}".format(datetime.strftime(now, "%Y-%m-%d")),
        'Attachments': [{"ContentType": "text/xml",
                         "Filename": file_name,
                         "Content": xml_b64encode}],
        'Html-part': render_template('mails/payments_xml_email.html', file_name=file_name, file_hash=checksum.hex())
    }


def make_payment_details_email(csv: str) -> dict:
    now = datetime.utcnow()
    csv_b64encode = base64.b64encode(csv.encode('utf-8')).decode()
    return {
        'FromEmail': 'support.passculture@beta.gouv.fr',
        'FromName': "pass Culture Pro",
        'Subject': "Détails des paiements pass Culture Pro - {}".format(datetime.strftime(now, "%Y-%m-%d")),
        'Attachments': [{"ContentType": "text/csv",
                         "Filename": "details_des_paiements_{}.csv".format(datetime.strftime(now, "%Y%m%d")),
                         "Content": csv_b64encode}],
        'Html-part': ""
    }


def make_payments_report_email(not_processable_csv: str, error_csv: str, grouped_payments: Dict) -> Dict:
    now = datetime.utcnow()
    not_processable_csv_b64encode = base64.b64encode(not_processable_csv.encode('utf-8')).decode()
    error_csv_b64encode = base64.b64encode(error_csv.encode('utf-8')).decode()
    formatted_date = datetime.strftime(now, "%Y-%m-%d")
    number_of_payments_for_one_status = lambda key_value: len(key_value[1])
    total_number_of_payments = sum(map(number_of_payments_for_one_status, grouped_payments.items()))

    return {
        'Subject': "Récapitulatif des paiements pass Culture Pro - {}".format(formatted_date),
        "FromEmail": 'support.passculture@beta.gouv.fr',
        "FromName": "pass Culture Pro",
        'Attachments': [
            {
                "ContentType": "text/csv",
                "Filename": "paiements_non_traitables_{}.csv".format(formatted_date),
                "Content": not_processable_csv_b64encode
            },
            {
                "ContentType": "text/csv",
                "Filename": "paiements_en_erreur_{}.csv".format(formatted_date),
                "Content": error_csv_b64encode
            }
        ],
        'Html-part': render_template(
            'mails/payments_report_email.html',
            date_sent=formatted_date,
            total_number=total_number_of_payments,
            grouped_payments=grouped_payments
        )
    }


def make_wallet_balances_email(csv: str) -> dict:
    now = datetime.utcnow()
    csv_b64encode = base64.b64encode(csv.encode('utf-8')).decode()
    return {
        'FromEmail': 'support.passculture@beta.gouv.fr',
        'FromName': "pass Culture Pro",
        'Subject': "Soldes des utilisateurs pass Culture - {}".format(datetime.strftime(now, "%Y-%m-%d")),
        'Attachments': [{"ContentType": "text/csv",
                         "Filename": "soldes_des_utilisateurs_{}.csv".format(datetime.strftime(now, "%Y%m%d")),
                         "Content": csv_b64encode}],
        'Html-part': ""
    }


def make_activation_users_email(csv: str) -> dict:
    now = datetime.utcnow()
    csv_b64encode = base64.b64encode(csv.encode('utf-8')).decode()
    return {
        'FromEmail': 'support.passculture@beta.gouv.fr',
        'FromName': "pass Culture Pro",
        'Subject': "Liste des utilisateurs créés pour l'activation du pass Culture - {}".format(
            datetime.strftime(now, "%Y-%m-%d")),
        'Attachments': [{"ContentType": "text/csv",
                         "Filename": "liste_des_utilisateurs_{}.csv".format(datetime.strftime(now, "%Y%m%d")),
                         "Content": csv_b64encode}],
        'Html-part': ""
    }


def make_venue_validation_confirmation_email(venue):
    html = render_template('mails/venue_validation_confirmation_email.html', venue=venue)
    return {
        'Subject': 'Validation du rattachement du lieu "{}" à votre structure "{}"'.format(venue.name,
                                                                                           venue.managingOfferer.name),
        'FromEmail': 'support.passculture@beta.gouv.fr',
        'FromName': "pass Culture pro",
        'Html-part': html
    }


def compute_email_html_part_and_recipients(email_html_part, recipients):
    recipients_string = ", ".join(recipients)
    if feature_send_mail_to_users_enabled():
        email_to = recipients_string
    else:
        email_html_part = '<p>This is a test (ENV={environment}). In production, email would have been sent to : {recipients}</p>{html_part}'.format(
            environment=ENV, recipients=recipients_string, html_part=email_html_part)
        email_to = 'passculture-dev@beta.gouv.fr'
    return email_html_part, email_to


def parse_email_addresses(addresses: str) -> List[str]:
    if not addresses:
        addresses = []
    elif ',' in addresses:
        addresses = [a.strip() for a in addresses.split(',')]
    elif ';' in addresses:
        addresses = [a.strip() for a in addresses.split(';')]
    else:
        addresses = [addresses]

    return [a for a in addresses if a]


def make_offer_creation_notification_email(offer: Offer, author: User, pro_origin_url: str) -> dict:
    humanized_offer_id = humanize(offer.id)
    link_to_offer = f'{pro_origin_url}/offres/{humanized_offer_id}'
    html = render_template('mails/offer_creation_notification_email.html', offer=offer, author=author,
                           link_to_offer=link_to_offer)
    location_information = offer.venue.departementCode or 'numérique'
    return {'Html-part': html,
            'To': ['support.passculture@beta.gouv.fr'],
            'FromEmail': 'support.passculture@beta.gouv.fr',
            'FromName': 'pass Culture',
            'Subject': f'[Création d’offre - {location_information}] {offer.eventOrThing.name}'}


def _generate_reservation_email_html_subject(booking):
    stock = booking.stock
    user = booking.user
    venue = stock.resolvedOffer.venue
    stock_description = _get_stock_description(stock)
    booking_is_on_event = stock.eventOccurrence == None

    if booking_is_on_event:
        email_subject = 'Confirmation de votre commande pour {}'.format(stock_description)
        email_html = render_template('mails/user_confirmation_email_thing.html',
                                     user=user,
                                     booking_token=booking.token,
                                     thing_name=stock.resolvedOffer.thing.name,
                                     thing_reference=stock.resolvedOffer.thing.idAtProviders,
                                     venue=venue)
    else:
        date_in_tz = _get_event_datetime(stock)
        formatted_date_time = format_datetime(date_in_tz)
        email_subject = 'Confirmation de votre réservation pour {}'.format(stock_description)
        email_html = render_template('mails/user_confirmation_email_event.html',
                                     user=user,
                                     booking_token=booking.token,
                                     event_occurrence_name=stock.eventOccurrence.offer.event.name,
                                     formatted_date_time=formatted_date_time,
                                     venue=venue
                                     )

    return email_html, email_subject


def _generate_user_driven_cancellation_email_for_user(user, stock):
    venue = stock.resolvedOffer.venue
    if stock.eventOccurrence == None:
        email_subject = 'Annulation de votre commande pour {}'.format(stock.resolvedOffer.thing.name)
        email_html = render_template('mails/user_cancellation_email_thing.html',
                                     user=user,
                                     thing_name=stock.resolvedOffer.thing.name,
                                     thing_reference=stock.resolvedOffer.thing.idAtProviders,
                                     venue=venue)
    else:
        date_in_tz = _get_event_datetime(stock)
        formatted_date_time = format_datetime(date_in_tz)
        email_html = render_template('mails/user_cancellation_email_event.html',
                                     user=user,
                                     event_occurrence_name=stock.eventOccurrence.offer.event.name,
                                     venue=venue,
                                     formatted_date_time=formatted_date_time)
        email_subject = 'Annulation de votre réservation pour {} le {}'.format(
            stock.eventOccurrence.offer.event.name,
            formatted_date_time
        )
    return email_html, email_subject


def _get_event_datetime(stock):
    if stock.eventOccurrence.offer.venue.departementCode is not None:
        date_in_utc = stock.eventOccurrence.beginningDatetime
        date_in_tz = utc_datetime_to_dept_timezone(date_in_utc,
                                                   stock.eventOccurrence.offer.venue.departementCode)

    else:
        date_in_tz = stock.eventOccurrence.beginningDatetime
    return date_in_tz


def _get_stock_description(stock):
    if stock.eventOccurrence:
        date_in_tz = _get_event_datetime(stock)
        description = '{} le {}'.format(stock.eventOccurrence.offer.event.name,
                                        format_datetime(date_in_tz))
    elif stock.resolvedOffer.thing:
        description = str(stock.resolvedOffer.thing.name)

    return description
