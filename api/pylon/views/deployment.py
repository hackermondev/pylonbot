import functools
import json
from typing import TypeVar, Callable, Optional, List

from sanic import Blueprint, response
from sanic.response import HTTPResponse
from sanic.request import Request
from sanic.log import logger
from pydantic import BaseModel, validator

from pylon.config import config
from pylon.database import ModelNotFound
from pylon.models.user import User, UserConnectedAccountQueries
from pylon.models.deployment import (
    GuildDeployment,
    GuildDeploymentQueries,
    DeploymentStatus,
)
from pylon.models.script import Script, ScriptQueries
from pylon.lib.auth import authorized
from pylon.lib.snowflake import snowflake
from pylon.lib.sandbox import get_sandbox_client

from pylon.lib.tasks import DeploymentKey, CronTask
from pylon.helpers.guild import GuildHelper
from pylon.helpers.deployment import DeploymentHelper

deployment_blueprint = Blueprint("deployment")


F = TypeVar("F", bound=Callable[..., response.HTTPResponse])


def with_deployment():
    def decorator(f: F) -> Callable[..., response.HTTPResponse]:
        @functools.wraps(f)
        async def decorated_function(
            request: Request, user: User, deployment_id: int, **kwargs
        ):
            async with request.app.db.acquire() as conn:
                try:
                    deployment = await GuildDeploymentQueries.get_one(
                        conn, id=deployment_id
                    )
                except ModelNotFound:
                    return response.text("could not find deployment", status=404)

                discord_account = await UserConnectedAccountQueries.get_discord_account_by_user_id(
                    conn, user_id=user.id
                )

            can_manage = await GuildHelper.can_manage(
                deployment.guild_id, int(discord_account.provider_id)
            )
            if not can_manage:
                return response.text("user not authorized to edit this deployment", 403)

            kwargs["deployment"] = deployment
            return await f(request, user=user, **kwargs)

        return decorated_function

    return decorator


@deployment_blueprint.route("/deployments/<deployment_id:int>")
@authorized()
@with_deployment()
async def route_get_deployment(
    request: Request, user: User, deployment: GuildDeployment
) -> HTTPResponse:
    return await DeploymentHelper.serialize(request, deployment)


class ScriptProjectFile(BaseModel):
    path: str
    content: str


class ScriptProject(BaseModel):
    files: List[ScriptProjectFile]

    @validator("files")
    def files_must_contain_items(cls, files):
        if not len(files):
            raise ValueError("project must contain files")
        return files


class DeploymentScriptBody(BaseModel):
    contents: str
    project: ScriptProject


class DeploymentUpdateBody(BaseModel):
    script: Optional[DeploymentScriptBody]


@deployment_blueprint.route("/deployments/<deployment_id:int>", methods=["POST"])
@authorized()
@with_deployment()
async def route_update_deployment(
    request: Request, user: User, deployment: GuildDeployment
) -> HTTPResponse:
    if len(request.body) > config.max_script_body_size:
        return response.json({"msg": "body size too large"}, status=400)

    data = request.json
    if not data:
        return response.json({"msg": "missing json body"}, status=400)

    body = DeploymentUpdateBody(**data)

    # Update the script
    if body.script:
        new_script_id = await snowflake.get()

        # Validate the request via the sandbox executor
        result = await get_sandbox_client().validate_script(
            id=str(new_script_id),
            contents=body.script.contents,
            bot_id=str(deployment.bot_id),
            guild_id=str(deployment.guild_id),
        )
        if not result.success:
            return response.json({"msg": result.message}, status=400)

        script_config = json.dumps(
            {
                "enabled": True,
                "events": list(result.events),
                "tasks": result.tasks.to_dict(),
            }
        )

        if len(list(result.tasks.cron_tasks)) > 5:
            return response.json(
                {"msg": "maximum of 5 cron tasks exceeded"}, status=400
            )

        cron_tasks = [
            CronTask(name=task.name, cron_string=task.cron_string)
            for task in result.tasks.cron_tasks
        ]

        deployment_key = DeploymentKey(
            id=deployment.id,
            revision=deployment.revision,
            bot_id=deployment.bot_id,
            guild_id=deployment.guild_id,
        )

        # If the script registers any tasks, validate and collect any errors
        if len(cron_tasks):
            validate_response = await DeploymentHelper.validate_tasks(
                deployment_key=deployment_key, cron_tasks=cron_tasks
            )

            if len(list(validate_response.errors)) > 0:
                first = validate_response.errors[0]
                return response.json(
                    {"msg": f"{first.task_name}: {first.error}"}, status=400
                )

        new_script = Script(
            id=new_script_id,
            bot_id=config.discord_bot_id,
            guild_id=deployment.guild_id,
            user_id=user.id,
            contents=body.script.contents,
            is_draft=False,
            project=body.script.project.json(),
        )

        # The behavior below follows some important implementation constraints to
        #  make sure we have a semi-sane state across services. Before any deployment
        #  data is synced to downstream services, we guarantee its updated in Postgres
        #  and etcd. If any errors occur while syncing to downstream services (e.g. tasks)
        #  we simply bubble these errors up to the client but do NOT rollback the
        #  deployment update.
        async with request.app.db.acquire() as conn:
            async with conn.transaction():
                await ScriptQueries.create(
                    conn, script=new_script,
                )

                status = deployment.status
                if deployment.script_id is None:
                    assert deployment.status == DeploymentStatus.DISABLED
                    status = DeploymentStatus.ENABLED

                deployment = await GuildDeploymentQueries.update(
                    conn,
                    id=deployment.id,
                    revision=deployment.revision,
                    script_id=new_script_id,
                    config=script_config,
                    status=status,
                )

            await DeploymentHelper.publish(deployment)

    errors = []

    try:
        await DeploymentHelper.publish_tasks(
            deployment_key=deployment_key, cron_tasks=cron_tasks
        )
    except Exception:
        logger.error(
            f"Failed to publish TASKS for deployment {deployment.id}", exc_info=True
        )
        errors.append(
            "Failed to register tasks: your tasks for this deployment may not fire until it is republished."
            "Please try again later."
        )

    return await DeploymentHelper.serialize(
        request, deployment, script=new_script, errors=errors
    )
