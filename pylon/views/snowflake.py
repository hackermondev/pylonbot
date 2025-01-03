from sanic import Blueprint
from sanic.response import HTTPResponse
from sanic.request import Request
from pylon.lib.json import json_response
from pylon.lib.snowflake import snowflake

snowflake_blueprint = Blueprint("snowflake")


@snowflake_blueprint.route("/snowflake")
async def route_snowflake(request: Request) -> HTTPResponse:
    return json_response({"snowflake": await snowflake.get()})
