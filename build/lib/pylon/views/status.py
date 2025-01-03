from sanic import Blueprint
from sanic.response import HTTPResponse
from sanic.request import Request
from pylon.lib.json import json_response

status_blueprint = Blueprint("status")


@status_blueprint.route("/status")
async def route_status(request: Request) -> HTTPResponse:
    return json_response({"status": "ok"})
