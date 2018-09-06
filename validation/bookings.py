from datetime import datetime

from models import ApiErrors
from models.api_errors import ResourceGoneError


def check_has_stock_id(stock_id):
    if stock_id is None:
        api_errors = ApiErrors()
        api_errors.addError('stockId', 'Vous devez préciser un identifiant d\'offre')
        raise api_errors


def check_has_quantity(quantity):
    if quantity is None:
        api_errors = ApiErrors()
        api_errors.addError('quantity', 'Vous devez préciser une quantité pour la réservation')
        raise api_errors


def check_existing_stock(stock):
    if stock is None:
        api_errors = ApiErrors()
        api_errors.addError('stockId', 'stockId ne correspond à aucun stock')
        raise api_errors


def check_can_book_free_offer(stock, user):
    if not user.canBookFreeOffers and stock.price == 0:
        api_errors = ApiErrors()
        api_errors.addError('cannotBookFreeOffers', 'L\'utilisateur n\'a pas le droit de réserver d\'offres gratuites')
        raise api_errors


def check_offer_is_active(stock, offerer):
    soft_deleted_stock = stock.isSoftDeleted
    inactive_offerer = not offerer.isActive
    soft_deleted_event_occurrence = stock.eventOccurrence and stock.eventOccurrence.isSoftDeleted

    if soft_deleted_stock or inactive_offerer or soft_deleted_event_occurrence:
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
        api_errors.addError('email', 'Vous devez préciser l\'email de l\'utilisateur quand vous n\'êtes pas connecté(e)')
        raise api_errors


def check_booking_not_cancelled(booking):
    if booking.isCancelled:
        resource_gone_error = ResourceGoneError()
        resource_gone_error.addError('booking', 'Cette réservation a été annulée')
        raise resource_gone_error


def check_booking_not_already_validated(booking):
    if booking.isValidated:
        resource_gone_error = ResourceGoneError()
        resource_gone_error.addError('booking', 'Cette réservation a déjà été validée')
        raise resource_gone_error



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
