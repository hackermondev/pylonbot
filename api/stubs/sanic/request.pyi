from typing import Dict, Any, Optional, List
from types import SimpleNamespace
from sanic import Sanic

class Request:
    raw_url: bytes
    app: Sanic
    headers: Dict[str, str]
    version: Any
    method: str
    transport: Any
    ctx: SimpleNamespace
    scheme: str
    body: bytes
    @property
    def json(self) -> Optional[Dict[Any, Any]]: ...
    @property
    def args(self) -> Dict[str, List[str]]: ...
    @property
    def cookies(self) -> Dict[str, str]: ...
