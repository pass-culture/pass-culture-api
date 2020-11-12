from pcapi import settings
from pcapi.utils import requests


class ReCaptchaException(Exception):
    pass


def validate_recaptcha_token(token: str, original_action: str) -> bool:
    if not token:
        return False

    params = {"secret": settings.RECAPTCHA_SECRET, "response": token}
    api_response = requests.post(settings.RECAPTCHA_API_URL, data=params)

    if api_response.status_code != 200:
        raise ReCaptchaException(f"Couldn't reach recaptcha api: {api_response.status_code} {api_response.text}")

    json_response = api_response.json()

    errors_list = []
    for error in json_response.get("error-codes", []):
        if error in settings.RECAPTCHA_ERROR_CODES:
            errors_list.append(settings.RECAPTCHA_ERROR_CODES[error])
        else:
            errors_list.append(error)
    if errors_list:
        raise ReCaptchaException(f"Encountered the following error(s): {errors_list}")

    if json_response["success"]:
        action = json_response.get("action", "")
        if action != original_action:
            raise ReCaptchaException(f"The action '{action}' does not match '{original_action}' from the form")

        score = json_response.get("score", 0)
        return score >= settings.RECAPTCHA_REQUIRED_SCORE

    raise ReCaptchaException("This is not a valid reCAPTCHA token")
