import asyncpg
import argparse
import asyncio
import logging

from typing import Optional
from itsdangerous import TimestampSigner
from oauthlib.oauth2 import WebApplicationClient
from grpclib.exceptions import GRPCError
from sanic import Sanic
from sanic.request import Request
from sanic.response import HTTPResponse
from sanic.log import logger
from pydantic.error_wrappers import ValidationError

from sentry_sdk.integrations.logging import LoggingIntegration, ignore_logger
from sentry_sdk.integrations.sanic import SanicIntegration
from sentry_sdk.hub import init as sentry_init
from sentry_sdk.api import configure_scope

from .database import ModelNotFound
from .lib.json import json_response
from .models.user import UserQueries, UserSession
from .config import config

from .views.status import status_blueprint
from .views.snowflake import snowflake_blueprint
from .views.runtime import runtime_blueprint
from .views.auth import auth_blueprint
from .views.user import user_blueprint
from .views.guild import guild_blueprint
from .views.deployment import deployment_blueprint

app = Sanic(name="pylon")
app.register_blueprint(status_blueprint)
app.register_blueprint(snowflake_blueprint)
app.register_blueprint(runtime_blueprint)
app.register_blueprint(auth_blueprint)
app.register_blueprint(user_blueprint)
app.register_blueprint(guild_blueprint)
app.register_blueprint(deployment_blueprint)

logging.getLogger().setLevel(logging.INFO)
log = logging.getLogger("pylon")


@app.listener("before_server_start")
async def setup(app: Sanic, loop):
    ignore_logger("hypercorn.access")
    sentry_logging = LoggingIntegration(
        level=logging.WARNING, event_level=logging.ERROR,
    )
    sentry_init(
        config.sentry_dsn,
        environment=config.environment,
        integrations=[sentry_logging, SanicIntegration()],
    )

    app.oauth = WebApplicationClient(config.discord_oauth_key)
    app.signer = TimestampSigner(config.secret_key)

    for idx in range(3):
        try:
            app.db = await asyncpg.create_pool(dsn=config.postgres_pylon)
        except ConnectionRefusedError:
            logger.warning(
                "Failed to initialize asyncpg pool on startup, waiting a bit and then trying again.",
                exc_info=True,
            )
            await asyncio.sleep(idx + 1)
            continue
        break
    else:
        raise Exception("asyncpg pool creation failed; is postgres ok?")


@app.listener("after_server_stop")
async def teardown(app: Sanic, loop):
    await app.db.close()


@app.middleware("request")
async def auth_middleware(request: Request) -> Optional[HTTPResponse]:
    request.ctx.user = None

    if "Authorization" not in request.headers:
        return None

    session_id = UserSession.verify_jwt(
        config.session_secret, request.headers["Authorization"]
    )
    try:
        async with request.app.db.acquire() as conn:
            request.ctx.user = await UserQueries.get_for_session_id(
                conn, session_id=session_id
            )
            request.ctx.session_id = session_id

        with configure_scope() as scope:
            scope.user = request.ctx.user.dict()

    except ModelNotFound:
        return json_response({"message": "bad auth"}, status=403)

    return None


@app.exception(ValidationError)
async def handle_validation_error(request, exception):
    logger.error(f"Encountered ValidationError: {exception.errors()}")
    return json_response(
        {"type": "validation", "errors": exception.errors()}, status=400
    )


@app.exception(GRPCError)
async def handle_grpc_error(request, exception):
    logger.error(f"Encountered GRPCError: {exception.message}")
    return json_response({"message": exception.message}, status=500)


if __name__ == "__main__":
    parser = argparse.ArgumentParser("pylon")
    parser.add_argument("--host", default="0.0.0.0")
    parser.add_argument("--port", default=8020)
    parser.add_argument("--debug", action="store_true", default=False)
    args = parser.parse_args()

    app.run(host=args.host, port=args.port, debug=args.debug)
