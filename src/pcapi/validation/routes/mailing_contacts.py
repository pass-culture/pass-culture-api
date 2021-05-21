from pcapi.models import ApiErrors


def validate_save_mailing_contact_request(json: dict):
    if "email" not in json or not json["email"]:
        errors = ApiErrors()
        errors.add_error("email", "L'email est manquant")
        raise errors

    if "dateOfBirth" not in json or not json["dateOfBirth"]:
        errors = ApiErrors()
        errors.add_error("date_of_birth", "La date de naissance est manquante")
        raise errors
