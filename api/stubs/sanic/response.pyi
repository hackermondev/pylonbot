from typing import Any, Dict, Callable, Union, List

HTTPResponse: Any

def json(
    body: Union[Dict[Any, Any], List[Any]],
    status: int = ...,
    headers: Dict[str, str] = ...,
    content_type: str = ...,
    dumps: Callable[[Any], bytes] = ...,
    **kwargs: Dict[Any, Any],
) -> HTTPResponse: ...
def text(
    body: str,
    status: int = ...,
    headers: Dict[str, str] = ...,
    content_type: str = ...,
) -> HTTPResponse: ...
def html(
    body: str, status: int = ..., headers: Dict[str, str] = ...,
) -> HTTPResponse: ...
def redirect(
    to: str, headers: Dict[str, str] = ..., status: int = ..., content_type: str = ...,
) -> HTTPResponse: ...
