async def test_user_get(test_cli, user, user_connected_account, user_session_headers):
    request, response = await test_cli.get("/user", headers=user_session_headers)
    assert response.status_code == 200
    assert response.json() == {
        "id": str(user.id),
        "lastSeenAt": user.last_seen_at.isoformat() + "+00:00",
        "avatar": user_connected_account.provider_avatar,
        "displayName": user_connected_account.provider_name,
        "hasAccess": True,
    }


async def test_user_get_guilds(
    test_cli,
    user,
    user_connected_account,
    user_session_headers,
    mock_shardclient_get_guild,
    guild,
):
    request, response = await test_cli.get("/user/guilds", headers=user_session_headers)
    assert response.status_code == 200
    assert response.json() == [
        {"id": str(guild.id), "icon": None, "name": "Mock Shard Guild"}
    ]
