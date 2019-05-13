from models import ApiErrors, Offer


def check_offer_offerer_exists(offerer):
    if offerer is None:
        api_errors = ApiErrors()
        api_errors.addError('offerId', 'l\'offreur associé à cette offre est inconnu')
        raise api_errors


def check_event_occurrence_offerer_exists(offerer):
    if offerer is None:
        api_errors = ApiErrors()
        api_errors.addError('eventOccurrenceId', 'l\'offreur associé à cet évènement est inconnu')
        raise api_errors


def check_request_has_offer_id(request_data: dict):
    if 'offerId' not in request_data:
        raise ApiErrors({'offerId': ['Ce paramètre est obligatoire']})


def check_dates_are_allowed_on_new_stock(request_data: dict, offer: Offer):
    if offer.isThing:
        _forbid_dates_on_stock_for_thing_offer(request_data)
    else:
        if request_data.get('endDatetime', None) is None:
            raise ApiErrors({'endDatetime': ['Ce paramètre est obligatoire']})

        if request_data.get('beginningDatetime', None) is None:
            raise ApiErrors({'beginningDatetime': ['Ce paramètre est obligatoire']})

        if request_data.get('bookingLimitDatetime', None) is None:
            raise ApiErrors({'bookingLimitDatetime': ['Ce paramètre est obligatoire']})


def check_dates_are_allowed_on_existing_stock(request_data: dict, offer: Offer):
    if offer.isThing:
        _forbid_dates_on_stock_for_thing_offer(request_data)
    else:
        if 'endDatetime' in request_data and request_data['endDatetime'] is None:
            raise ApiErrors({'endDatetime': ['Ce paramètre est obligatoire']})

        if 'beginningDatetime' in request_data and request_data['beginningDatetime'] is None:
            raise ApiErrors({'beginningDatetime': ['Ce paramètre est obligatoire']})

        if 'bookingLimitDatetime' in request_data and request_data['bookingLimitDatetime'] is None:
            raise ApiErrors({'bookingLimitDatetime': ['Ce paramètre est obligatoire']})


def _forbid_dates_on_stock_for_thing_offer(request_data):
    if 'beginningDatetime' in request_data or 'endDatetime' in request_data:
        raise ApiErrors(
            {'global': [
                'Impossible de mettre des dates de début et fin si l\'offre ne porte pas sur un évenement'
            ]})

