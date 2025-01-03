from typing import Optional
from grpclib.client import Channel
from rpc.sandbox.v1 import SandboxStub, ValidationResult, Script as SandboxScript
from pylon.config import config

__all__ = ["get_sandbox_client", SandboxScript, ValidationResult, SandboxStub]


_sandbox_client: Optional[SandboxStub] = None


def get_sandbox_client() -> SandboxStub:
    global _sandbox_client
    if _sandbox_client is None:
        host, port = config.endpoint_sandbox_dispatch.split(":", 1)
        channel = Channel(host, int(port))
        _sandbox_client = SandboxStub(channel)
    return _sandbox_client
