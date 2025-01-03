import random
import string
import base64
import json

from typing import Any, Callable, TypeVar
from functools import wraps
from sanic.request import Request
from sanic import response
from pylon.helpers.user import UserHelper
from pylon.lib.json import json_response

F = TypeVar("F", bound=Callable[..., response.HTTPResponse])


def generate_random_auth_nonce() -> str:
    return "".join(random.choice(string.ascii_letters) for _ in range(32))


def sign_object(signer, obj: Any) -> bytes:
    return signer.sign(base64.b64encode(json.dumps(obj).encode("utf-8")))


def unsign_object(signer, raw: str) -> Any:
    return json.loads(base64.b64decode(signer.unsign(raw)).decode("utf-8"))


def authorized(requires_beta=True):
    def decorator(f: F) -> Callable[..., response.HTTPResponse]:
        @wraps(f)
        async def decorated_function(
            request: Request, *args, **kwargs
        ) -> response.HTTPResponse:
            if not request.ctx.user:
                return json_response({"message": "not authorized"}, status=403)
            if requires_beta:
                can_access_beta = await UserHelper.can_access_beta(
                    request.ctx.user, request
                )
                if not can_access_beta:
                    return json_response(
                        {"message": "beta access required"}, status=401
                    )

            kwargs["user"] = request.ctx.user
            return await f(request, *args, **kwargs)

        return decorated_function

    return decorator
