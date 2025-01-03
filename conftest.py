import pytest
import inspect
import asyncio

from sanic.testing import SanicASGITestClient
from datetime import datetime


from pylon.config import config
from pylon.server import app as pylon_app, setup
from pylon.models.bot import Bot, BotQueries
from pylon.models.user import (
    User,
    UserQueries,
    UserSession,
    UserSessionQueries,
    UserConnectedAccount,
    UserConnectedAccountQueries,
)
from pylon.models.guild import Guild, GuildQueries
from pylon.models.deployment import (
    GuildDeployment,
    GuildDeploymentQueries,
    DeploymentStatus,
    DeploymentType,
)
from pylon.models.script import Script, ScriptQueries
from pylon.helpers.guild import GuildHelper
from pylon.lib.snowflake import SnowflakeClient
from pylon.lib.shardclient import shardclient


@pytest.fixture
def snowflake():
    async def get_snowflake():
        return await SnowflakeClient(config.endpoint_snowflake).get()

    return get_snowflake


@pytest.fixture(scope="session")
def app(event_loop):
    event_loop.run_until_complete(setup(pylon_app, event_loop))
    return pylon_app


@pytest.fixture(scope="session")
async def conn(app):
    conn = await app.db.acquire()
    yield conn
    await conn.close()


@pytest.fixture(scope="function")
async def user(conn, user_connected_account):
    user = User(id=user_connected_account.user_id, last_seen_at=datetime.utcnow())
    await UserQueries.create(
        conn, user=user,
    )
    return user


@pytest.fixture(scope="function")
async def user_connected_account(conn, snowflake):
    connected_account = UserConnectedAccount(
        id=(await snowflake()),
        user_id=await snowflake(),
        last_authed_at=datetime.utcnow(),
        provider="discord",
        provider_id=(await snowflake()),
        provider_name="Test User",
        provider_token="{}",
    )
    await UserConnectedAccountQueries.create(
        conn, user_connected_account=connected_account
    )
    return connected_account


@pytest.fixture
def mock_guild_can_manage(monkeypatch):
    async def mock_can_manage(*args, **kwargs):
        return True

    monkeypatch.setattr(GuildHelper, "can_manage", mock_can_manage)


@pytest.fixture
def mock_shardclient_get_guild(monkeypatch):
    async def mock_get_guild(guild_id):
        return {
            "id": guild_id,
            "name": "Mock Shard Guild",
            "icon": None,
        }

    monkeypatch.setattr(shardclient, "get_guild", mock_get_guild)


@pytest.fixture(scope="function")
async def user_session(conn, user, snowflake):
    session = UserSession(id=(await snowflake()), user_id=user.id, ip=0)
    await UserSessionQueries.create(conn, user_session=session)
    return session


@pytest.fixture(scope="function")
async def user_session_headers(user_session):
    return {"Authorization": user_session.generate_jwt()}


@pytest.fixture(scope="function")
async def bot(conn, user, snowflake):
    bot_id = await snowflake()
    bot = Bot(
        id=bot_id,
        bot_token="test",
        client_id="test",
        client_secret="test",
        user_id=user.id,
    )
    await BotQueries.create(conn, bot=bot)
    return bot


@pytest.fixture(scope="function")
async def script(conn, deployment, user, snowflake):
    script = Script(
        id=(await snowflake()),
        bot_id=config.discord_bot_id,
        guild_id=deployment.guild_id,
        user_id=user.id,
        contents="",
        project="",
    )
    await ScriptQueries.create(conn, script=script)
    return script


@pytest.fixture(scope="function")
async def deployment(conn, guild, snowflake):
    deployment = GuildDeployment(
        id=(await snowflake()),
        bot_id=config.discord_bot_id,
        guild_id=guild.id,
        type=DeploymentType.SCRIPT,
        status=DeploymentStatus.DISABLED,
        name="test deployment",
        config="{}",
        revision=0,
    )
    await GuildDeploymentQueries.create(conn, guild_deployment=deployment)
    return deployment


@pytest.fixture(scope="function")
async def guild(conn, user, snowflake):
    guild = Guild(id=(await snowflake()), user_id=user.id)
    await GuildQueries.create(conn, guild=guild)
    return guild


@pytest.fixture(scope="session")
async def test_cli(app):
    client = SanicASGITestClient(app)
    yield client


@pytest.fixture(scope="session")
def event_loop():
    return asyncio.get_event_loop()


def pytest_collection_modifyitems(session, config, items):
    for item in items:
        if isinstance(item, pytest.Function) and inspect.iscoroutinefunction(
            item.function
        ):
            item.add_marker(pytest.mark.asyncio)
