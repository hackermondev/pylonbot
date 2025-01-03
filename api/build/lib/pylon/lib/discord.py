from httpx import AsyncClient, Timeout

_discord_client_timeout = Timeout(10, read_timeout=20)
discord_api = AsyncClient(http2=True, timeout=_discord_client_timeout)
