from typing import Optional
from datetime import datetime

from pydantic import validator
from pylon.lib.query import Query
from pylon.database import Model

from enum import IntEnum


class DeploymentType(IntEnum):
    SCRIPT = 0
    APP = 1


class DeploymentStatus(IntEnum):
    DISABLED = 0
    ENABLED = 1


class GuildDeployment(Model):
    class Meta:
        table_name = "guild_deployments"

    id: int
    bot_id: int
    guild_id: int
    type: DeploymentType
    status: DeploymentStatus
    name: str
    app_id: Optional[int]
    script_id: Optional[int]
    last_updated_at: Optional[datetime]
    config: str
    revision: int

    @validator("app_id", pre=True, always=True)
    def fix_app_id_nulls(cls, app_id):
        if app_id == 0:
            return None
        return app_id


class GuildDeploymentQueries:
    get_one = Query(GuildDeployment).select().where("id = {.id}").fetchone().build()

    create = Query(GuildDeployment).insert().build()

    update = (
        Query(GuildDeployment)
        .update("script_id", "config", "status", revision="revision + 1")
        .where("id = {.id} AND revision = {.revision}")
        .returning()
        .fetchone()
        .build()
    )

    get_for_guild_id = (
        Query(GuildDeployment)
        .select()
        .where("guild_id = {.guild_id}")
        .fetchall()
        .build()
    )
