import pytest
from pylon.config import config


@pytest.mark.parametrize(
    "action,scope",
    [
        ("join_guild", "identify+guilds.join"),
        ("list_guilds", "identify+guilds"),
        ("auth", "identify"),
    ],
)
async def test_auth_discord(test_cli, action, scope):
    request, response = await test_cli.get(
        "/auth/discord", params={"action": action}, allow_redirects=False
    )
    assert response.status == 302
    assert response.headers["location"].startswith(
        f"https://discordapp.com/api/oauth2/authorize?response_type=code&client_id={config.discord_oauth_key}"
        f"&redirect_uri=http%3A%2F%2Flocalhost%3A3000%2Fapi%2Fauth%2Fdiscord%2Fcallback&scope={scope}&state="
    )
    assert response.headers["set-cookie"].startswith("s=")
    assert response.headers["set-cookie"].endswith("; Path=/; Max-Age=300")
