async def test_snowflake(test_cli):
    request, response = await test_cli.get("/snowflake")
    assert response.status_code == 200
    assert isinstance(response.json()["snowflake"], str)
    assert int(response.json()["snowflake"]) > 1  # :^)
