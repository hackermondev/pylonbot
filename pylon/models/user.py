import jwt

from typing import Optional
from datetime import datetime
from pylon.config import config
from pylon.database import Model
from pylon.lib.query import Query


class User(Model):
    class Meta:
        table_name = "users"

    id: int
    email: Optional[str]
    password: Optional[str]
    last_seen_at: datetime


class UserSession(Model):
    class Meta:
        table_name = "user_sessions"

    id: int
    user_id: int
    ip: int

    def generate_jwt(self) -> str:
        return jwt.encode(
            {"userId": str(self.user_id), "sessionId": str(self.id)},
            config.session_secret,
            algorithm="HS256",
        ).decode("utf-8")

    @staticmethod
    def verify_jwt(secret, raw) -> int:
        return int(jwt.decode(raw, secret, algorithms="HS256")["sessionId"])


class UserConnectedAccount(Model):
    class Meta:
        table_name = "user_connected_accounts"

    id: int
    user_id: int
    last_authed_at: datetime
    provider: str
    provider_id: str
    provider_name: str
    provider_avatar: Optional[str]
    provider_token: str


class UserQueries:
    create = Query(User).insert().build()

    get_one = Query(User).select().where("id = {.id}").fetchone().build()

    get_for_session_id = (
        Query(User)
        .select(alias="users")
        .join(UserSession, "user_sessions.user_id = users.id")
        .where("user_sessions.id = {session_id}")
        .fetchone()
        .build()
    )


class UserSessionQueries:
    create = Query(UserSession).insert().build()


class UserConnectedAccountQueries:
    create = Query(UserConnectedAccount).insert().build()

    get_discord_account_by_user_id = (
        Query(UserConnectedAccount)
        .select()
        .where("user_id = {.user_id} AND provider = 'discord'")
        .fetchone()
        .build()
    )

    update_discord_account_by_provider_id = (
        Query(UserConnectedAccount)
        .update("provider_token", "provider_avatar", "provider_name", "last_authed_at")
        .where("provider_id = {.provider_id} AND provider = 'discord'")
        .returning()
        .fetchone()
        .build()
    )

    update_discord_account_by_user_id = (
        Query(UserConnectedAccount)
        .update("provider_token", "last_authed_at")
        .where("user_id = {.user_id} AND provider = 'discord'")
        .returning()
        .fetchone()
        .build()
    )
