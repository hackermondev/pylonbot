from typing import Any, Optional, List

import jwt
from sanic.request import Request

from pylon.config import config
from pylon.lib.shardclient import shardclient
from pylon.lib.json import json_response
from pylon.lib.tasks import get_tasks_client
from pylon.models.deployment import GuildDeployment, DeploymentStatus
from pylon.models.script import ScriptQueries, Script
from pylon.lib.etcd import etcd


def take(obj, *keys):
    return {k: obj[k] for k in keys}


class DeploymentHelper:
    @staticmethod
    async def serialize(
        request: Request,
        deployment: GuildDeployment,
        script: Optional[Script] = None,
        errors: Optional[List[str]] = None,
    ) -> Any:
        res = deployment.dict(
            include={
                "id",
                "bot_id",
                "type",
                "status",
                "name",
                "app_id",
                "config",
                "revision",
            }
        )

        workbench_token = jwt.encode(
            {
                "scriptId": str(deployment.script_id),
                "sessionId": str(request.ctx.session_id),
            },
            config.session_secret,
            algorithm="HS256",
        ).decode("utf-8")
        res["workbench_url"] = f"{config.endpoint_workbench_ws}/ws/{workbench_token}"

        if not script and deployment.script_id:
            async with request.app.db.acquire() as conn:
                script = await ScriptQueries.get_one(conn, id=deployment.script_id)

        res["script"] = script.dict(include={"id", "project"}) if script else None

        discord_guild = await shardclient.get_guild(deployment.guild_id)
        assert discord_guild
        res["guild"] = take(discord_guild, "id", "name", "icon")

        if errors is not None:
            res["errors"] = errors

        return json_response(res)

    @staticmethod
    async def validate_tasks(deployment_key, cron_tasks) -> Any:
        return await get_tasks_client().validate_deployment_tasks(
            deployment_key=deployment_key, cron_tasks=cron_tasks
        )

    @staticmethod
    async def publish(deployment: GuildDeployment):
        if deployment.status == DeploymentStatus.ENABLED:
            await etcd.set(f"/deployments/{deployment.id}", deployment.json())

    @staticmethod
    async def publish_tasks(deployment_key, cron_tasks) -> Any:
        return await get_tasks_client().publish_deployment_tasks(
            deployment_key=deployment_key, cron_tasks=cron_tasks
        )
