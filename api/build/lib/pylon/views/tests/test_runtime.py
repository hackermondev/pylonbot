async def test_runtime_get_bot(bot, test_cli):
    request, response = await test_cli.get(
        f"/runtime/bots/{bot.id}", headers={"X-RPC-Key": "test"}
    )
    assert response.status == 200
    assert response.json()["id"] == str(bot.id)


async def test_runtime_get_script(script, test_cli):
    request, response = await test_cli.get(
        f"/runtime/scripts/{script.id}", headers={"X-RPC-Key": "test"}
    )
    assert response.status == 200
    assert response.json()["id"] == str(script.id)


async def test_runtime_get_deployment(deployment, test_cli):
    request, response = await test_cli.get(
        f"/runtime/deployments/{deployment.id}", headers={"X-RPC-Key": "test"}
    )
    assert response.status == 200
    assert response.json()["id"] == str(deployment.id)
