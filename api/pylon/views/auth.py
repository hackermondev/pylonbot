import json
from urllib.parse import urlparse

from datetime import datetime
from sanic import Blueprint, response
from sanic.request import Request
from sanic.response import HTTPResponse
from oauthlib.common import urldecode
from pylon.config import config
from pylon.models.user import (
    User,
    UserSession,
    UserQueries,
    UserConnectedAccount,
    UserSessionQueries,
    UserConnectedAccountQueries,
)
from pylon.database import ModelNotFound
from pylon.lib.auth import sign_object, unsign_object, generate_random_auth_nonce
from pylon.lib.json import json_response
from pylon.lib.shardclient import shardclient
from pylon.lib.snowflake import snowflake
from pylon.lib.discord import discord_api

auth_blueprint = Blueprint("auth")


@auth_blueprint.route("/auth/discord")
async def route_auth_discord(request: Request) -> HTTPResponse:
    callback = request.args.get("callback")
    if callback:
        url = urlparse(callback[0])

        hostname = url.netloc.rsplit(":", 1) if url.port else url.netloc
        if hostname != "localhost" and hostname != "127.0.0.1":
            return json_response({"message": "bad callback URL"}, status=400)

    action = request.args.get("action", "auth")
    state = [generate_random_auth_nonce(), action, callback]

    if action == "join_guild":
        scope = "identify guilds.join"
    elif action == "list_guilds":
        scope = "identify guilds"
    elif action == "auth":
        scope = "identify"
    else:
        return json_response({"message": "bad action"}, status=400)

    signed_state = sign_object(request.app.signer, state)

    redirect_uri = request.app.oauth.prepare_request_uri(
        "https://discordapp.com/api/oauth2/authorize",
        redirect_uri=config.endpoint_api_public + "/auth/discord/callback",
        scope=scope,
        state=signed_state,
    )

    if "s" in request.cookies:
        del request.cookies["s"]

    res = response.redirect(redirect_uri)
    res.cookies["s"] = signed_state.decode("utf-8")
    res.cookies["s"]["max-age"] = 60 * 5
    return res


@auth_blueprint.route("/auth/discord/callback")
async def route_auth_discord_callback(request: Request) -> HTTPResponse:
    raw_state = request.cookies.get("s")
    if not raw_state:
        return json_response({"message": "bad state"}, status=400)

    del request.cookies["s"]

    if raw_state != request.args.get("state"):
        return json_response({"message": "state mismatch"}, status=400)

    state = unsign_object(request.app.signer, raw_state)

    error = request.args.get("error")
    if error:
        return json_response({"message": error}, status=400)

    code = request.args.get("code")
    if not code:
        return json_response({"message": "invalid code"}, status=400)

    token_exchange_body = request.app.oauth.prepare_request_body(
        code=request.args.get("code"),
        redirect_uri=config.endpoint_api_public + "/auth/discord/callback",
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
    assert isinstance(access_token, dict)

    res = await discord_api.get(
        "https://discordapp.com/api/v7/users/@me",
        headers={
            "Authorization": f"{access_token['token_type']} {access_token['access_token']}",
        },
    )
    if not res.status_code == 200:
        return json_response({"message": "error fetching account details"})

    discord_user = res.json()
    assert isinstance(discord_user, dict)

    if state[1] == "join_guild":
        member_url = f"https://discordapp.com/api/v7/guilds/{config.pylon_guild_id}/members/{discord_user['id']}"
        headers = {"Authorization": f"Bot {config.discord_bot_token}"}
        member = await shardclient.get_guild_member(
            config.pylon_guild_id, discord_user["id"]
        )
        if member is not None:
            if "628887351619485706" in member["roles"]:
                return response.text("already have beta access", 400)

            res = await discord_api.put(
                f"{member_url}/roles/{config.pylon_beta_role_id}", headers=headers,
            )
            if res.status_code == 204:
                return response.html(_popup_content_message("", True))
        else:
            res = await discord_api.put(
                member_url,
                json={
                    "access_token": access_token["access_token"],
                    "roles": [str(config.pylon_beta_role_id)],
                },
                headers=headers,
            )
            if res.status_code in (201, 204):
                return response.html(_popup_content_message("", True))

        return response.html(
            _popup_content_message(
                "We couldn't add the Beta role to your account. Please try again!",
                False,
            ),
            status=500,
        )

    async with request.app.db.acquire() as conn:
        try:
            existing_account = await UserConnectedAccountQueries.update_discord_account_by_provider_id(
                conn,
                provider_id=discord_user["id"],
                provider_token=json.dumps(access_token),
                provider_name=discord_user["username"],
                provider_avatar=discord_user["avatar"],
                last_authed_at=datetime.utcnow(),
            )
            user_id = existing_account.user_id
        except ModelNotFound:
            user_id = await snowflake.get()
            connected_account_id = await snowflake.get()

            async with conn.transaction():
                await UserQueries.create(
                    conn,
                    user=User(
                        id=user_id,
                        email=None,
                        password=None,
                        last_seen_at=datetime.utcnow(),
                    ),
                )

                await UserConnectedAccountQueries.create(
                    conn,
                    user_connected_account=UserConnectedAccount(
                        id=connected_account_id,
                        user_id=user_id,
                        provider="discord",
                        provider_id=discord_user["id"],
                        provider_name=discord_user["username"],
                        provider_avatar=discord_user["avatar"],
                        provider_token=json.dumps(access_token),
                        last_authed_at=datetime.utcnow(),
                    ),
                )

        session_id = await snowflake.get()
        session = UserSession(id=session_id, user_id=user_id, ip=0)
        await UserSessionQueries.create(conn, user_session=session)

        jwt = session.generate_jwt()

        if state[2]:
            return response.html(_popup_content_callback(jwt, state[2]))
        return response.html(_popup_content(jwt))


POPUP_CONTENT = """
<script type="text/javascript">
    window.opener.setToken("{token}");
    window.close();
</script>
"""

POPUP_CONTENT_MESSAGE = """
<script type="text/javascript">
    window.opener.setToken(null, "{message}", {silent});
    window.close();
</script>`

"""

POPUP_CONTENT_CALLBACK = """
<script type="text/javascript">
    var url = "{callback_url}";
    var request = new XMLHttpRequest();
    request.open("POST", url, true);
    request.send("{token}");
    request.onreadystatechange = function () {
        if (request.readyState !== XMLHttpRequest.DONE) {
            return;
        }
        if (request.status === 200) {
            document.write("Authentication complete. You may now close this window.");
            window.close();
        } else {
            document.write("Could not authenticate! Try again.");
        }
    }
</script>
"""


def _popup_content(token: str) -> str:
    return POPUP_CONTENT.format(token=token)


def _popup_content_message(message: str, silent: bool) -> str:
    return POPUP_CONTENT_MESSAGE.format(
        message=message, silent="true" if silent else "false"
    )


def _popup_content_callback(token: str, callback_url: str) -> str:
    return POPUP_CONTENT_CALLBACK.format(token=token, callback_url=callback_url)
