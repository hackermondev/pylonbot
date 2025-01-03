from typing import Optional
from pydantic import BaseSettings


class PylonConfig(BaseSettings):
    environment: str
    rpckey: str

    sentry_dsn: Optional[str]
    postgres_pylon: str
    discord_oauth_key: str
    discord_oauth_secret: str
    discord_bot_token: str
    discord_bot_id: int

    secret_key: str
    session_secret: str
    endpoint_sandbox_dispatch: str
    endpoint_quotas: str
    endpoint_tasks: str
    etcd_endpoints: str

    endpoint_snowflake: str
    endpoint_sharder: str
    endpoint_api_public: str
    endpoint_workbench_ws: str

    # API Specific
    pylon_guild_id: int
    pylon_beta_role_id: int

    max_script_body_size: int = 5000000


config = PylonConfig()
