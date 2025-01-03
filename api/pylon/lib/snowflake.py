from httpx import AsyncClient
from pylon.config import config


class SnowflakeClient:
    def __init__(self, snowflake_endpoint: str):
        self._client = AsyncClient(base_url=snowflake_endpoint)

    async def get(self) -> int:
        res = await self._client.get("/")
        return int(res.text)


snowflake = SnowflakeClient(config.endpoint_snowflake)
