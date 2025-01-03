from typing import Optional
from sanic import response
from sanic.request import Request
from pylon.config import config


async def validate_rpc_request(request: Request) -> Optional[response.HTTPResponse]:
    if request.headers.get("X-RPC-Key") != config.rpckey:
        return response.text("not found", status=404)

    return None
