from functools import wraps
from typing import Any
from typing import Callable
from typing import Optional
from typing import Type

from flask import Response
from flask import make_response
from flask import request
from pydantic import BaseModel
from spectree import Response as SpectreeResponse
from spectree.spec import SpecTree

from pcapi.flask_app import api as default_api
from pcapi.models import ApiErrors


def _make_json_response(
    content: Optional[BaseModel],
    status_code: int,
    by_alias: bool,
    exclude_none: bool = False,
) -> Response:
    """serializes model, creates JSON response with given status code"""
    if status_code == 204:
        return make_response("", 204)

    if not content:
        raise ApiErrors({"configuration": "You need to provide a response body model if the status code is not 204"})

    json_content = content.json(exclude_none=exclude_none, by_alias=by_alias)

    response = make_response(json_content, status_code)
    response.mimetype = "application/json"
    return response


def spectree_serialize(  # pylint: disable=dangerous-default-value
    headers: Type[BaseModel] = None,
    cookies: Type[BaseModel] = None,
    response_model: Type[BaseModel] = None,
    tags: tuple = (),
    before: Callable = None,
    after: Callable = None,
    response_by_alias: bool = True,
    exclude_none: bool = False,
    on_success_status: int = 200,
    on_error_statuses: list[int] = [],
    api: SpecTree = default_api,
) -> Callable[[Any], Any]:
    """A decorator that serialize/deserialize and validate input/output

    Args:
        cookies (Type[BaseModel], optional): Describes the cookies. Defaults to None.
        response_model (Type[BaseModel], optional): Describes the http response Model. Defaults to None.
        tags (tuple, optional): list of tags’ string. Defaults to ().
        before (Callable, optional): hook executed before the spectree validation. Defaults to None.
        after (Callable, optional): hook executed after the spectree validation. Defaults to None.
        response_by_alias (bool, optional): whether or not the alias generator will be used. Defaults to True.
        exclude_none (bool, optional): whether or not to remove the none values. Defaults to False.
        on_success_status (int, optional): status returned when the validation is a success. Defaults to 200.
        on_error_statuses (list[int], optional): list of possible error statuses. Defaults to [].
        api (SpecTree, optional): [description]. Defaults to default_api.

    Returns:
        Callable[[Any], Any]: [description]
    """

    def decorate_validation(route: Callable[..., Any]) -> Callable[[Any], Any]:
        body_in_kwargs = route.__annotations__.get("body")
        query_in_kwargs = route.__annotations__.get("query")
        form_in_kwargs = route.__annotations__.get("form")

        if 403 not in on_error_statuses:
            on_error_statuses.append(403)

        spectree_response = SpectreeResponse(*[f"HTTP_{on_error_status}" for on_error_status in on_error_statuses])

        if on_success_status == 204:
            spectree_response.codes.append(f"HTTP_{on_success_status}")

        if response_model:
            spectree_response.code_models[f"HTTP_{on_success_status}"] = response_model

        @wraps(route)
        @api.validate(
            query=query_in_kwargs,
            headers=headers,
            cookies=cookies,
            resp=spectree_response,
            tags=tags,
            before=before,
            after=after,
            json=body_in_kwargs,
        )
        def sync_validate(*args: dict, **kwargs: dict) -> Response:
            body_params = request.get_json()
            query_params = request.args
            form = request.form
            if body_in_kwargs:
                kwargs["body"] = body_in_kwargs(**body_params)
            if query_in_kwargs:
                kwargs["query"] = query_in_kwargs(**query_params)
            if form_in_kwargs:
                kwargs["form"] = form_in_kwargs(**form)

            result = route(*args, **kwargs)
            return _make_json_response(
                content=result, status_code=on_success_status, by_alias=response_by_alias, exclude_none=exclude_none
            )

        return sync_validate

    return decorate_validation
