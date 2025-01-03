from sanic import Blueprint, response
from sanic.request import Request
from sanic.response import HTTPResponse

from pylon.database import ModelNotFound
from pylon.models.script import ScriptQueries
from pylon.models.bot import BotQueries
from pylon.models.deployment import GuildDeploymentQueries
from pylon.lib.json import json_response
from ..lib.rpc import validate_rpc_request

runtime_blueprint = Blueprint("runtime")
runtime_blueprint.middleware(validate_rpc_request)


@runtime_blueprint.route("/runtime/bots/<bot_id:int>")
async def route_get_bot(request: Request, bot_id: int) -> HTTPResponse:
    try:
        async with request.app.db.acquire() as conn:
            bot = await BotQueries.get_one(conn, id=bot_id)
    except ModelNotFound:
        return response.text("", status=404)

    return json_response(bot)


@runtime_blueprint.route("/runtime/scripts/<script_id:int>")
async def route_get_script(request: Request, script_id: int) -> HTTPResponse:
    try:
        async with request.app.db.acquire() as conn:
            script = await ScriptQueries.get_one(conn, id=script_id)
    except ModelNotFound:
        return response.text("", status=404)

    return json_response(script)


@runtime_blueprint.route("/runtime/deployments/<deployment_id:int>")
async def route_get_deployment(request: Request, deployment_id: int) -> HTTPResponse:
    try:
        async with request.app.db.acquire() as conn:
            deployment = await GuildDeploymentQueries.get_one(conn, id=deployment_id)
    except ModelNotFound:
        return response.text("", status=404)

    return json_response(deployment)
