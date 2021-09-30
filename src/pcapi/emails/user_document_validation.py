from pcapi import settings
from pcapi.connectors.beneficiaries.id_check_middleware import IdCheckErrorCodes


class DocumentValidationUnknownError(Exception):
    pass


def build_data_for_document_verification_error(code: str) -> dict:
    error_codes_switch = {
        IdCheckErrorCodes.UNREAD_DOCUMENT.value: _build_unread_document_data,
        IdCheckErrorCodes.UNREAD_MRZ_DOCUMENT.value: _build_invalid_document_data,
        IdCheckErrorCodes.INVALID_DOCUMENT_DATE.value: _build_invalid_document_date_data,
        IdCheckErrorCodes.INVALID_DOCUMENT.value: _build_invalid_document_data,
        IdCheckErrorCodes.INVALID_AGE.value: _build_invalid_age_data,
    }

    handler = error_codes_switch.get(code, _build_unread_document_data)
    return handler()


def _build_unread_document_data() -> dict:
    return {
        "MJ-TemplateID": 2958557,
        "MJ-TemplateLanguage": True,
        "Mj-campaign": "jouve-error-unread-document",
        "Vars": {
            "url": settings.DMS_USER_URL,
        },
    }


def _build_invalid_document_date_data() -> dict:
    return {
        "MJ-TemplateID": 2958563,
        "MJ-TemplateLanguage": True,
        "Mj-campaign": "jouve-error-invalid-document-date",
        "Vars": {
            "url": settings.DMS_USER_URL,
        },
    }


def _build_invalid_document_data() -> dict:
    return {
        "MJ-TemplateID": 2958584,
        "MJ-TemplateLanguage": True,
        "Mj-campaign": "jouve-error-invalid-document",
        "Vars": {},
    }


def _build_invalid_age_data() -> dict:
    return {
        "MJ-TemplateID": 2958585,
        "MJ-TemplateLanguage": True,
        "Mj-campaign": "jouve-error-invalid-age",
        "Vars": {},
    }
