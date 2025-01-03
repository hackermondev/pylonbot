from typing import Optional
from grpclib.client import Channel
from rpc.quotas.v1 import QuotasStub, ManagedGuildUsageRequest, ManagedGuildUsageReport
from pylon.config import config

__all__ = [
    "get_quotas_client",
    QuotasStub,
    ManagedGuildUsageRequest,
    ManagedGuildUsageReport,
]


_quotas_client: Optional[QuotasStub] = None


def get_quotas_client() -> QuotasStub:
    global _quotas_client
    if _quotas_client is None:
        host, port = config.endpoint_quotas.split(":", 1)
        channel = Channel(host, int(port))
        _quotas_client = QuotasStub(channel)
    return _quotas_client
