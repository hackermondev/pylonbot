from typing import List

import random
from httpx import AsyncClient
from pylon.config import config


class ETCDClient:
    def __init__(self, endpoints: List[str]):
        self._endpoints = endpoints
        self._client = AsyncClient()

    async def set(self, key: str, value: str):
        url = random.choice(self._endpoints)
        res = await self._client.put(url + f"/v2/keys/{key}", params={"value": value})
        res.raise_for_status()

    async def delete(self, key: str):
        url = random.choice(self._endpoints)
        res = await self._client.delete(url + f"/v2/keys/{key}")
        res.raise_for_status()


etcd = ETCDClient(config.etcd_endpoints.split(","))
