from models import ApiErrors, RightsType


def check_allowed_changes_for_user(data):
    changes_allowed = {
        'culturalSurveyId',
        'departementCode',
        'email',
        'needsToFillCulturalSurvey',
        'phoneNumber',
        'postalCode',
        'publicName',
    }
    changes_asked = set(data)
    api_errors = ApiErrors()
    changes_not_allowed = changes_asked.difference(changes_allowed)
    if changes_not_allowed:
        for change in changes_not_allowed:
            api_errors.add_error(change, 'Vous ne pouvez pas changer cette information')
        raise api_errors


def check_valid_signup(request):
    contact_ok = request.json.get('contact_ok')
    password = request.json.get('password')
    email = request.json.get('email')
    if email is None:
        errors = ApiErrors()
        errors.add_error('email', 'Vous devez renseigner un email.')
        raise errors
    if not contact_ok or _contact_ok_is_not_checked(contact_ok):
        errors = ApiErrors()
        errors.add_error('contact_ok', 'Vous devez obligatoirement cocher cette case.')
        raise errors

    if not password:
        errors = ApiErrors()
        errors.add_error('password', 'Vous devez renseigner un mot de passe.')
        raise errors


def check_valid_signin(identifier: str, password: str):
    errors = ApiErrors()
    errors.status_code = 401

    if identifier is None:
        errors.add_error('identifier', 'Identifiant manquant')
    if password is None:
        errors.add_error('password', 'Mot de passe manquant')

    errors.maybe_raise()


def _contact_ok_is_not_checked(contact_ok):
    contact_ok_is_not_checked_as_bool = contact_ok is not True
    contact_ok_is_not_checked_as_str = str(contact_ok).lower() != 'true'
    return contact_ok_is_not_checked_as_bool and contact_ok_is_not_checked_as_str


def check_user_can_validate_bookings(self, offerer_id):
    if self.is_authenticated:
        if self.hasRights(RightsType.editor, offerer_id):
            return True
        else:
            api_errors = ApiErrors()
            api_errors.add_error('global', 'Cette contremarque n\'a pas été trouvée')
            raise api_errors
    else:
        return False
