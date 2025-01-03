import simplejson

from pylon.database import Model
from typing import Dict, List, Union, Any
from sanic.response import HTTPResponse
from pydantic.json import pydantic_encoder


def json_response(
    obj: Union[Dict[Any, Any], List[Any], str, int, Model], status=200
) -> HTTPResponse:
    data = simplejson.dumps(obj, default=pydantic_encoder, bigint_as_string=True)
    return HTTPResponse(data, status=status, content_type="application/json")


def json_error(msg: str, status=400, **kwargs) -> HTTPResponse:
    kwargs["msg"] = msg
    return json_response(kwargs, status=status)
