"""Optional HTTP Basic Auth guard for the web UI."""

from __future__ import annotations

import base64
import hmac
import os
from collections.abc import Awaitable, Callable

from fastapi import Request, Response
from fastapi.responses import PlainTextResponse

_EXEMPT_PATHS = {"/health"}
_REALM = 'Basic realm="Namensschmiede"'


def _configured_password() -> str:
    return os.getenv("APP_BASIC_AUTH_PASSWORD", "").strip()


def _configured_username() -> str:
    return os.getenv("APP_BASIC_AUTH_USERNAME", "admin").strip() or "admin"


def _auth_enabled() -> bool:
    return bool(_configured_password())


def _unauthorized_response() -> Response:
    return PlainTextResponse(
        "Authentication required.",
        status_code=401,
        headers={"WWW-Authenticate": _REALM},
    )


def _parse_basic_auth(header_value: str | None) -> tuple[str, str] | None:
    if not header_value:
        return None

    scheme, _, credentials = header_value.partition(" ")
    if scheme.lower() != "basic" or not credentials:
        return None

    try:
        decoded = base64.b64decode(credentials).decode("utf-8")
    except (ValueError, UnicodeDecodeError):
        return None

    username, separator, password = decoded.partition(":")
    if not separator:
        return None
    return username, password


def _is_authorized(request: Request) -> bool:
    parsed = _parse_basic_auth(request.headers.get("Authorization"))
    if parsed is None:
        return False

    username, password = parsed
    return hmac.compare_digest(username, _configured_username()) and hmac.compare_digest(
        password,
        _configured_password(),
    )


async def basic_auth_middleware(
    request: Request,
    call_next: Callable[[Request], Awaitable[Response]],
) -> Response:
    if not _auth_enabled() or request.url.path in _EXEMPT_PATHS:
        return await call_next(request)

    if not _is_authorized(request):
        return _unauthorized_response()

    return await call_next(request)
