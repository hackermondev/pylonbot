from pylon.config import config


async def test_deployment_get(
    deployment,
    user_session_headers,
    test_cli,
    mock_guild_can_manage,
    mock_shardclient_get_guild,
):
    request, response = await test_cli.get(
        f"/deployments/{deployment.id}", headers=user_session_headers,
    )
    assert response.status_code == 200
    assert response.json()["id"] == str(deployment.id)
    assert response.json()["workbench_url"].startswith(config.endpoint_workbench_ws)
    assert response.json()["guild"]["id"] == str(deployment.guild_id)
    assert response.json()["script"] is None
