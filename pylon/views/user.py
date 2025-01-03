import json
import asyncio

from sanic import Blueprint, response
from sanic.response import HTTPResponse
from sanic.request import Request

from pylon.lib.json import json_response
from pylon.helpers.user import UserHelper
from pylon.lib.auth import authorized
from pylon.models.user import User, UserConnectedAccountQueries
from pylon.models.guild import GuildQueries
from pylon.lib.shardclient import shardclient
from pylon.lib.discord import discord_api

user_blueprint = Blueprint("user")


@user_blueprint.route("/user")
@authorized(requires_beta=False)
async def route_user(request: Request, user: User) -> HTTPResponse:
    async with request.app.db.acquire() as conn:
        discord_account = await UserConnectedAccountQueries.get_discord_account_by_user_id(
            conn, user_id=user.id,
        )

    return json_response(
        {
            "id": user.id,
            "lastSeenAt": user.last_seen_at.isoformat(),
            "avatar": discord_account.provider_avatar,
            "displayName": discord_account.provider_name,
            "hasAccess": await UserHelper.can_access_beta(user, request),
        }
    )


@user_blueprint.route("/user/guilds")
@authorized()
async def route_user_guilds(request: Request, user: User) -> HTTPResponse:
    async with request.app.db.acquire() as conn:
        guild_ids = [
            i.id for i in await GuildQueries.get_for_user_id(conn, user_id=user.id)
        ]

    guild_futures = [shardclient.get_guild(guild_id) for guild_id in guild_ids]
    guilds = [
        {"id": str(guild["id"]), "name": guild["name"], "icon": guild["icon"]}
        for guild in await asyncio.gather(*guild_futures)
        if guild is not None
    ]

    return json_response(guilds)


@user_blueprint.route("/user/guilds/available")
@authorized()
async def route_user_guilds_available(request: Request, user: User) -> HTTPResponse:
    async with request.app.db.acquire() as conn:
        discord_account = await UserConnectedAccountQueries.get_discord_account_by_user_id(
            conn, user_id=user.id,
        )

    discord_account = await UserHelper.maybe_refresh_discord_credentials(
        user, discord_account, request
    )

    token = json.loads(discord_account.provider_token)

    headers = {"Authorization": f"{token['token_type']} {token['access_token']}"}
    res = await discord_api.get(
        "https://discordapp.com/api/v7/users/@me/guilds", headers=headers
    )

    if res.status_code != 200:
        return response.text("unauthorized", 401)

    guilds = res.json()

    user_guilds = [
        {
            "id": str(guild["id"]),
            "name": guild["name"],
            "icon": guild["icon"],
            "permissions": guild["permissions"],
        }
        for guild in guilds
    ]

    return json_response(user_guilds)
