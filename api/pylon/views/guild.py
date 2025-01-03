import time
import json
import functools
import asyncio

from asyncpg import UniqueViolationError
from pydantic import BaseModel, validator
from typing import TypeVar, Callable
from sanic import Blueprint, response
from sanic.response import HTTPResponse
from sanic.request import Request
from oauthlib.common import urldecode
from datetime import datetime


from pylon.config import config
from pylon.database import ModelNotFound
from pylon.models.guild import Guild, GuildQueries
from pylon.models.deployment import (
    GuildDeployment,
    GuildDeploymentQueries,
    DeploymentStatus,
    DeploymentType,
)
from pylon.models.user import (
    User,
    UserQueries,
    UserConnectedAccountQueries,
)
from pylon.helpers.guild import GuildHelper
from pylon.helpers.deployment import DeploymentHelper
from pylon.lib.quotas import get_quotas_client
from pylon.lib.snowflake import snowflake
from pylon.lib.auth import (
    authorized,
    sign_object,
    unsign_object,
    generate_random_auth_nonce,
)
from pylon.lib.json import json_response, json_error
from pylon.lib.shardclient import shardclient
from pylon.lib.discord import discord_api

guild_blueprint = Blueprint("guild")

STATS_PERIOD = 24 * 7 * 60 * 60  # 1 week
SCRIPT_CONTENTS_LIMIT = 3000000  # Spencer math for 3mb
MAX_SCRIPT_BODY_SIZE = 5000000  # b1nzy math for 5mb


F = TypeVar("F", bound=Callable[..., response.HTTPResponse])


def with_guild():
    def decorator(f: F) -> Callable[..., response.HTTPResponse]:
        @functools.wraps(f)
        async def decorated_function(
            request: Request, user: User, guild_id: int, **kwargs
        ):
            async with request.app.db.acquire() as conn:
                try:
                    guild = await GuildQueries.get_one(
                        conn, id=guild_id, user_id=user.id
                    )
                except ModelNotFound:
                    return response.text("could not find guild", status=404)

                discord_account = await UserConnectedAccountQueries.get_discord_account_by_user_id(
                    conn, user_id=user.id,
                )

            can_manage = await GuildHelper.can_manage(
                guild_id, int(discord_account.provider_id)
            )
            if not can_manage:
                return response.text("user not authorized to edit this guild", 403)

            kwargs["guild"] = guild
            return await f(request, user=user, **kwargs)

        return decorated_function

    return decorator


@guild_blueprint.route("/guilds/<guild_id:int>")
@authorized()
@with_guild()
async def route_get_guild(request: Request, user: User, guild: Guild) -> HTTPResponse:
    async with request.app.db.acquire() as conn:
        deployments_query = GuildDeploymentQueries.get_for_guild_id(
            conn, guild_id=guild.id
        )

        (discord_guild, deployments) = await asyncio.gather(
            shardclient.get_guild(guild.id), deployments_query,
        )
        if not discord_guild:
            return response.text("not found", status=404)

    discord_guild["deployments"] = deployments
    return json_response(discord_guild)


@guild_blueprint.route("/guilds/<guild_id:int>/add")
@authorized()
async def route_add_guild(request: Request, user: User, guild_id: int) -> HTTPResponse:
    guild = await shardclient.get_guild(guild_id)
    if guild:
        async with request.app.db.acquire() as conn:
            discord_account = await UserConnectedAccountQueries.get_discord_account_by_user_id(
                conn, user_id=user.id,
            )

        can_manage = await GuildHelper.can_manage(
            guild_id, int(discord_account.provider_id)
        )
        if not can_manage:
            return response.text(
                "user does not have permissions to manage that guild", 400
            )

        async with request.app.db.acquire() as conn:
            try:
                await GuildQueries.create(
                    conn, guild=Guild(id=guild_id, user_id=user.id)
                )
            except UniqueViolationError:
                pass

        return json_response({"requiresGuildAuth": False, "guild": guild})

    state = sign_object(
        request.app.signer,
        [generate_random_auth_nonce(), "add_guild", (guild_id, user.id)],
    )

    redirect_uri = request.app.oauth.prepare_request_uri(
        "https://discordapp.com/api/oauth2/authorize",
        redirect_uri=config.endpoint_api_public + "/guild/callback",
        permissions=8,
        guild_id=guild_id,
        disable_guild_select="true",
        scope="bot",
        state=state,
    )

    return json_response({"requiresGuildAuth": True, "redirectUrl": redirect_uri})


@guild_blueprint.route("/guild/callback")
async def route_guild_callback(request: Request) -> HTTPResponse:
    if "state" not in request.args:
        return response.text("invalid state", status=400)

    state = unsign_object(request.app.signer, request.args["state"][0])
    if not state:
        return response.text("invalid state", status=400)

    (guild_id, user_id) = state[2]

    if request.args.get("guild_id") != str(guild_id):
        return response.text(
            "requested guild did not match the callback guild", status=400
        )

    async with request.app.db.acquire() as conn:
        try:
            await UserQueries.get_one(conn, id=user_id)
        except ModelNotFound:
            return response.text("could not fetch user from database", 500)

    code = request.args.get("code")
    if not code:
        return json_response({"message": "invalid code"}, status=400)

    token_exchange_body = request.app.oauth.prepare_request_body(
        code=request.args.get("code"),
        redirect_uri=config.endpoint_api_public + "/guild/callback",
        client_secret=config.discord_oauth_secret,
    )

    res = await discord_api.post(
        "https://discordapp.com/api/oauth2/token",
        data=dict(urldecode(token_exchange_body)),
    )

    if not res.status_code == 200:
        return json_response(
            {"message": f"discord error: {res.text} ({res.status_code})"}
        )

    access_token = res.json()

    async with request.app.db.acquire() as conn:
        await UserConnectedAccountQueries.update_discord_account_by_user_id(
            conn,
            user_id=user_id,
            provider_token=json.dumps(access_token),
            last_authed_at=datetime.utcnow(),
        )

        try:
            await GuildQueries.create(conn, guild=Guild(id=guild_id, user_id=user_id))
        except UniqueViolationError:
            pass

    return response.html(
        '<script type="text/javascript">window.opener.onGuildAddDone();window.close();</script>'
    )


@guild_blueprint.route("/guilds/<guild_id:int>/stats")
@authorized()
@with_guild()
async def route_guild_get_stats(
    request: Request, user: User, guild: Guild
) -> HTTPResponse:
    now = time.time()
    result = await get_quotas_client().get_managed_guild_usage(
        date_start=int(now - STATS_PERIOD),
        date_end=int(now),
        interval=86400,
        bot_id=config.discord_bot_id,
        guild_id=guild.id,
    )

    return json_response(result.to_dict()["intervals"])


class GuildAddDeploymentBody(BaseModel):
    name: str

    @validator("name")
    def validate_name_length(cls, name):
        if len(name) > 32:
            raise ValueError("name must be no more than 32 characters long")
        return name


@guild_blueprint.route("/guilds/<guild_id:int>/deployment", methods=["POST"])
@authorized()
@with_guild()
async def route_guild_add_deployment(
    request: Request, user: User, guild: Guild
) -> HTTPResponse:
    data = request.json
    assert isinstance(data, dict)
    body = GuildAddDeploymentBody(**data)

    deployment_id = await snowflake.get()

    async with request.app.db.acquire() as conn:
        try:
            deployment = GuildDeployment(
                id=deployment_id,
                bot_id=config.discord_bot_id,
                guild_id=guild.id,
                type=DeploymentType.SCRIPT,
                status=DeploymentStatus.DISABLED,
                name=body.name,
                config="{}",
                revision=0,
            )

            await GuildDeploymentQueries.create(conn, guild_deployment=deployment)
        except UniqueViolationError:
            # Temporary until multiple deployments are supported
            return json_error("This guild already has a deployment")

    return await DeploymentHelper.serialize(request, deployment)
