from typing import Dict, Any, List, Union, Optional
from httpx import AsyncClient
from pylon.config import config


class ShardClient:
    def __init__(self, bot_id: int, sharder_endpoint: str):
        self._base_url = f"{sharder_endpoint.rstrip('/')}/bots/{bot_id}/state"
        self._client = AsyncClient(http2=True)

    async def get(
        self, url: str, none_on_404=True
    ) -> Optional[Union[Dict[Any, Any], List[Any]]]:
        res = await self._client.get(self._base_url + url)
        if none_on_404 and res.status_code == 404:
            return None
        res.raise_for_status()
        return res.json()

    async def get_guild_member(
        self, guild_id: int, user_id: int
    ) -> Optional[Dict[str, Any]]:
        res = await self.get(f"/guilds/{guild_id}/members/{user_id}")
        if res:
            assert isinstance(res, dict)
            return res
        return None

    async def get_guild(self, guild_id: int) -> Optional[Dict[str, Any]]:
        res = await self.get(f"/guilds/{guild_id}")
        if res:
            assert isinstance(res, dict)
            return res
        return None


shardclient = ShardClient(config.discord_bot_id, config.endpoint_sharder)
