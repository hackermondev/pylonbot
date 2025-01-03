import json

from sanic.log import logger
from sanic.request import Request
from datetime import datetime, timedelta
from oauthlib.common import urldecode

from pylon.models.user import (
    User,
    UserConnectedAccount,
    UserConnectedAccountQueries,
)
from pylon.config import config
from pylon.lib.shardclient import shardclient
from pylon.lib.discord import discord_api


class UserHelper:
    @staticmethod
    async def can_access_beta(user: User, request: Request) -> bool:
        if config.environment in ("dev", "test"):
            return True

        async with request.app.db.acquire() as conn:
            discord_account = await UserConnectedAccountQueries.get_discord_account_by_user_id(
                conn, user_id=user.id
            )

        res = await shardclient.get_guild_member(
            config.pylon_guild_id, int(discord_account.provider_id)
        )
        if not res:
            return False

        return str(config.pylon_beta_role_id) in res["roles"]

    @staticmethod
    async def maybe_refresh_discord_credentials(
        user: User, discord_account: UserConnectedAccount, request: Request
    ) -> UserConnectedAccount:
        token = json.loads(discord_account.provider_token)

        # TODO: It appears some tokens aren't valid in our DB
        if "expires_in" not in token:
            return discord_account

        expires_at = discord_account.last_authed_at.replace(tzinfo=None) + timedelta(
            seconds=token["expires_in"]
        )
        if expires_at < datetime.utcnow():
            logger.info(
                f"Refreshing access token for user {user.id} (discord user id {discord_account.provider_id})"
            )

            refresh_body = request.app.oauth.prepare_refresh_body(
                refresh_token=token["refresh_token"],
                client_secret=config.discord_oauth_secret,
                client_id=config.discord_oauth_key,
                scope=token["scope"],
            )
            res = await discord_api.post(
                "https://discordapp.com/api/oauth2/token",
                data=dict(urldecode(refresh_body)),
            )
            try:
                res.raise_for_status()
            except Exception:
                logger.error("Failed to refresh discord token", exc_info=True)
                return discord_account

            access_token = res.json()

            async with request.app.db.acquire() as conn:
                return await UserConnectedAccountQueries.update_discord_account_by_user_id(
                    conn,
                    user_id=user.id,
                    provider_token=json.dumps(access_token),
                    last_authed_at=datetime.utcnow(),
                )

        return discord_account
