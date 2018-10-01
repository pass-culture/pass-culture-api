from datetime import datetime, timedelta

from models import ApiErrors
from models.api_errors import ResourceGoneError


def check_has_stock_id(stock_id):
    if stock_id is None:
        api_errors = ApiErrors()
        api_errors.addError('stockId', 'Vous devez préciser un identifiant d\'offre')
        raise api_errors


def check_has_quantity(quantity):
    if quantity is None or quantity <= 0:
        api_errors = ApiErrors()
        api_errors.addError('quantity', 'Vous devez préciser une quantité pour la réservation')
        raise api_errors


def check_existing_stock(stock):
    if stock is None:
        api_errors = ApiErrors()
        api_errors.addError('stockId', 'stockId ne correspond à aucun stock')
        raise api_errors


def check_not_soft_deleted_stock(stock):
    if stock.isSoftDeleted:
        api_errors = ApiErrors()
        api_errors.addError('stockId', "Cette date a été retirée. Elle n'est plus disponible.")
        raise api_errors


def check_can_book_free_offer(stock, user):
    if not user.canBookFreeOffers and stock.price == 0:
        api_errors = ApiErrors()
        api_errors.addError('cannotBookFreeOffers', 'L\'utilisateur n\'a pas le droit de réserver d\'offres gratuites')
        raise api_errors


def check_offer_is_active(stock, offerer):
    soft_deleted_stock = stock.isSoftDeleted
    inactive_offerer = not offerer.isActive
    inactive_offer = not stock.resolvedOffer.isActive
    soft_deleted_event_occurrence = stock.eventOccurrence and stock.eventOccurrence.isSoftDeleted

    if soft_deleted_stock or inactive_offerer or inactive_offer or soft_deleted_event_occurrence:
        api_errors = ApiErrors()
        api_errors.addError('stockId', "Cette offre a été retirée. Elle n'est plus valable.")
        raise api_errors


def check_stock_booking_limit_date(stock):
    stock_has_expired = stock.bookingLimitDatetime is not None and stock.bookingLimitDatetime < datetime.utcnow()

    if stock_has_expired:
        api_errors = ApiErrors()
        api_errors.addError('global', 'La date limite de réservation de cette offre est dépassée')
        raise api_errors


def check_expenses_limits(expenses, booking, stock):
    if stock.resolvedOffer.event:
        return None

    if stock.resolvedOffer.thing.isDigital:
        _check_digital_expense_limit(booking, expenses)
    else:
        _check_physical_expense_limit(booking, expenses)


def check_user_is_logged_in_or_email_is_provided(user, email):
    if not (user.is_authenticated or email):
        api_errors = ApiErrors()
        api_errors.addError('email',
                            'Vous devez préciser l\'email de l\'utilisateur quand vous n\'êtes pas connecté(e)')
        raise api_errors


def check_booking_is_usable(booking):
    resource_gone_error = ResourceGoneError()
    if booking.isUsed:
        resource_gone_error.addError('booking', 'Cette réservation a déjà été validée')
        raise resource_gone_error
    if booking.isCancelled:
        resource_gone_error.addError('booking', 'Cette réservation a été annulée')
        raise resource_gone_error


def check_booking_is_cancellable(booking, is_user_cancellation):
    api_errors = ApiErrors()
    if booking.isUsed:
        api_errors.addError('booking', "Impossible d\'annuler une réservation consommée")
        raise api_errors
    if booking.stock.eventOccurrence:
        two_days_before_event = booking.stock.eventOccurrence.beginningDatetime - timedelta(hours=48)
        if (datetime.utcnow() > two_days_before_event) and is_user_cancellation:
            api_errors.addError('booking',
                                "Impossible d\'annuler une réservation moins de 48h avant le début de l'évènement")
            raise api_errors

def check_email_and_offer_id_for_anonymous_user(email, offer_id):
    api_errors = ApiErrors()
    if not email:
        api_errors.addError('email',
                            "L'adresse email qui a servie à la réservation est obligatoire dans l'URL [?email=<email>]")
    if not offer_id:
        api_errors.addError('offer_id', "L'id de l'offre réservée est obligatoire dans l'URL [?offer_id=<id>]")
    if api_errors.errors:
        raise api_errors


def _check_physical_expense_limit(booking, expenses):
    new_expenses = expenses['physical']['actual'] + booking.amount * booking.quantity
    if new_expenses > expenses['physical']['max']:
        api_errors = ApiErrors()
        api_errors.addError('global', 'La limite de %s € pour les biens culturels ne vous permet pas ' \
                                      'de réserver' % expenses['physical']['max'])
        raise api_errors


def _check_digital_expense_limit(booking, expenses):
    new_expenses = expenses['digital']['actual'] + booking.amount * booking.quantity
    if new_expenses > expenses['digital']['max']:
        api_errors = ApiErrors()
        api_errors.addError('global', 'La limite de %s € pour les offres numériques ne vous permet pas ' \
                                      'de réserver' % expenses['digital']['max'])
        raise api_errors
