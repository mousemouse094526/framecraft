"""What a POST, PUT or PATCH body may be: JSON, or a raw file on the routes that list
`require_octet_stream` (ADR 0013, ADR 0028).

Both types force a CORS preflight, which the backend never answers, so no other site can
start a job or change a file; `multipart/form-data` is refused everywhere because a form
of another site can send it without one.
"""

from fastapi import Request

from backend.errors import ApiError

JSON = "application/json"
OCTET_STREAM = "application/octet-stream"


def media_type(request: Request) -> str:
    """The request's `Content-Type` without its parameters, lowercase; "" when none."""
    return request.headers.get("content-type", "").split(";")[0].strip().lower()


def require_octet_stream(request: Request) -> None:
    """A route's own dependency: its body is a raw file and nothing else (spoil D50, D55)."""
    if media_type(request) != OCTET_STREAM:
        raise ApiError(415, "unsupported_media_type", "ต้องส่งเป็นไฟล์ (application/octet-stream)")


def require_json(request: Request) -> None:
    """The app-wide dependency: every POST, PUT and PATCH is JSON, except a route that
    lists `require_octet_stream` itself, which then decides alone (ADR 0028)."""
    if request.method not in ("POST", "PUT", "PATCH") or _takes_raw_body(request):
        return
    if media_type(request) != JSON:
        # ApiError is the API's one refusal shape, `{"code", "message"}`.
        raise ApiError(415, "unsupported_media_type", "ต้องส่งเป็น JSON")


def _takes_raw_body(request: Request) -> bool:
    # The matched route is in the scope by the time a dependency runs. Only the decorator's
    # `dependencies=[Depends(require_octet_stream)]` counts, not one taken as a parameter.
    route = request.scope.get("route")
    return any(depends.dependency is require_octet_stream for depends in getattr(route, "dependencies", ()))
