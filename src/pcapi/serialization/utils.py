from typing import Any
from typing import Optional
from typing import Union

from flask import Request
from flask import Response
from pydantic import BaseModel
from pydantic import ValidationError
from pydantic import validator

from pcapi.models import ApiErrors
from pcapi.utils.human_ids import dehumanize
from pcapi.utils.human_ids import dehumanize_ids_list
from pcapi.utils.human_ids import humanize


def to_camel(string: str) -> str:
    components = string.split("_")
    return components[0] + "".join(x.title() for x in components[1:])


def before_handler(
    request: Request,  # pylint: disable=unused-argument
    response: Response,  # pylint: disable=unused-argument
    pydantic_error: Optional[ValidationError],
    _: Any,
) -> None:
    """Raises an ``ApiErrors` exception if input validation fails.

    This handler is automatically called through the ``spectree_serialize()`` decorator.
    """
    error_messages = {
        "type_error.integer": "Saisissez un nombre valide",
        "value_error.datetime": "Format de date invalide",
        "value_error.extra": "Vous ne pouvez pas changer cette information",
        "value_error.missing": "Ce champ est obligatoire",
    }

    if pydantic_error and pydantic_error.errors():
        api_errors = ApiErrors()
        for error in pydantic_error.errors():
            message = error_messages.get(error["type"], error["msg"])
            api_errors.add_error(error["loc"][0], message)
        raise api_errors


def humanize_id(id_to_humanize: Optional[Union[int, str]]) -> Optional[str]:
    if id_to_humanize is None:
        return None

    # This is because humanize_id will be called on a int the first time
    # and then on ids already humanized. humanize can't work with string
    if isinstance(id_to_humanize, int):
        return humanize(id_to_humanize)

    return str(id_to_humanize)


def dehumanize_id(id_to_dehumanize: Optional[Union[int, str]]) -> Optional[int]:
    if id_to_dehumanize is None:
        return None

    # This is because dehumanize_id will be called on a str the first time
    # and then on ids already dehumanized. dehumanize can't work with int
    if isinstance(id_to_dehumanize, str):
        return dehumanize(id_to_dehumanize)

    return int(id_to_dehumanize)


def cast_optional_str_to_int(optional_str: Optional[str]) -> Optional[int]:
    if isinstance(optional_str, str):
        return int(optional_str)

    return optional_str


def humanize_field(field_name: str) -> classmethod:
    return validator(field_name, pre=True, allow_reuse=True)(humanize_id)


def dehumanize_field(field_name: str) -> classmethod:
    return validator(field_name, pre=True, allow_reuse=True)(dehumanize_id)


def dehumanize_list_field(field_name: str) -> classmethod:
    return validator(field_name, pre=True, allow_reuse=True)(dehumanize_ids_list)


def cast_optional_field_str_to_int(field_name: str) -> classmethod:
    return validator(field_name, pre=True, allow_reuse=True)(cast_optional_str_to_int)


class InputBaseModel(BaseModel):
    class Config:
        alias_generator = to_camel
        extra = "forbid"
