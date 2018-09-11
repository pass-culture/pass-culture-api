import re
import secrets
import string
from datetime import datetime, timedelta

from models import ApiErrors
from utils.token import random_token

RESET_PASSWORD_TOKEN_LENGTH = 10


def check_new_password_validity(user, old_password, new_password):
    errors = ApiErrors()

    if not user.checkPassword(old_password):
        errors.addError('oldPassword', 'Votre ancien mot de passe est incorrect')
        raise errors

    if user.checkPassword(new_password):
        errors.addError('newPassword', 'Votre nouveau mot de passe est identique à l\'ancien')
        raise errors

def validate_change_password_request(json):
    errors = ApiErrors()

    if 'oldPassword' not in json:
        errors.addError('oldPassword', 'Ancien mot de passe manquant')
        raise errors

    if 'newPassword' not in json:
        errors.addError('newPassword', 'Nouveau mot de passe manquant')
        raise errors


def generate_reset_token(user):
    token = random_token(length=RESET_PASSWORD_TOKEN_LENGTH)
    user.resetPasswordToken = token
    user.resetPasswordTokenValidityLimit = datetime.utcnow() + timedelta(hours=24)


def validate_reset_request(request):
    if 'email' not in request.get_json():
        errors = ApiErrors()
        errors.addError('email', 'L\'email est manquant')
        raise errors

    if not request.get_json()['email']:
        errors = ApiErrors()
        errors.addError('email', 'L\'email renseigné est vide')
        raise errors


def validate_new_password_request(request):
    if 'token' not in request.get_json():
        errors = ApiErrors()
        errors.addError('token', 'Votre lien de changement de mot de passe est invalide.')
        raise errors

    if 'password' not in request.get_json():
        errors = ApiErrors()
        errors.addError('password', 'Vous devez renseigner un nouveau mot de passe.')
        raise errors


def check_reset_token_validity(user):
    if datetime.utcnow() > user.resetPasswordTokenValidityLimit:
        errors = ApiErrors()
        errors.addError('token',
                        'Votre lien de changement de mot de passe est périmé. Veuillez effecture une nouvelle demande.')
        raise errors


def check_password_strength(field_name, field_value):
    at_least_one_uppercase = '(?=.*?[A-Z])'
    at_least_one_lowercase = '(?=.*?[a-z])'
    at_least_one_digit = '(?=.*?[0-9])'
    min_length = '.{12,}'
    at_least_one_special_char = '(?=.*?[#~|=+><?!@$%^&*_-])'

    regex = '^' \
            + at_least_one_uppercase \
            + at_least_one_lowercase \
            + at_least_one_digit \
            + at_least_one_special_char \
            + min_length \
            + '$'

    if not re.match(regex, field_value):
        errors = ApiErrors()
        errors.addError(
            field_name,
            'Le mot de passe doit faire au moins 12 caractères et contenir à minima '
            '1 majuscule, 1 minuscule, 1 chiffre et 1 caractère spécial parmi _-&?~#|^@=+.$,<>%*!:;'
        )
        raise errors


def _random_alphanum_char():
    return secrets.choice(string.ascii_uppercase + string.digits)
