async def test_status(test_cli):
    request, response = await test_cli.get("/status")
    assert response.status_code == 200
    assert response.json() == {"status": "ok"}
