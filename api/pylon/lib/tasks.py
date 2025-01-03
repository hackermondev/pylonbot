from typing import Optional
from grpclib.client import Channel

from rpc.common.v1 import DeploymentKey
from rpc.tasks.v1 import TasksStub, CronTask, DeploymentTasks
from pylon.config import config

__all__ = [
    "get_tasks_client",
    DeploymentKey,
    TasksStub,
    CronTask,
    DeploymentTasks,
]


_tasks_client: Optional[TasksStub] = None


def get_tasks_client() -> TasksStub:
    global _tasks_client
    if _tasks_client is None:
        host, port = config.endpoint_tasks.split(":", 1)
        channel = Channel(host, int(port))
        _tasks_client = TasksStub(channel)
    return _tasks_client
