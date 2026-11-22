"""Keep simulated identities behind a loopback-only HTTP boundary."""

from ipaddress import ip_address
from urllib.parse import urlsplit

from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse
from starlette.middleware.base import RequestResponseEndpoint
from starlette.responses import Response


def install_local_boundary(application: FastAPI) -> None:
    @application.middleware("http")
    async def local_only(request: Request, call_next: RequestResponseEndpoint) -> Response:
        peer = request.client.host if request.client else ""
        # TestClient is an in-process ASGI transport, not a network address.
        testing = peer == "testclient"
        try:
            local_peer = testing or ip_address(peer).is_loopback
        except ValueError:
            local_peer = False
        try:
            hostname = request.url.hostname or ""
            local_host = hostname == "localhost" or (testing and hostname == "testserver")
            if not local_host:
                try:
                    local_host = ip_address(hostname).is_loopback
                except ValueError:
                    local_host = False
            origin = request.headers.get("origin")
            expected = urlsplit(str(request.url))
            supplied = urlsplit(origin) if origin else None
            same_origin = supplied is None or (
                supplied.scheme == expected.scheme
                and supplied.hostname == expected.hostname
                and (supplied.port or (443 if supplied.scheme == "https" else 80))
                == (expected.port or (443 if expected.scheme == "https" else 80))
                and not supplied.username
                and not supplied.password
                and supplied.path in {"", "/"}
                and not supplied.query
                and not supplied.fragment
            )
        except ValueError:
            local_host = same_origin = False
        if (
            not local_peer
            or not local_host
            or not same_origin
            or request.headers.get("sec-fetch-site") == "cross-site"
        ):
            return JSONResponse(
                {"detail": "This synthetic demo is available only on local loopback."},
                status_code=403,
                headers={"Cache-Control": "no-store", "X-Content-Type-Options": "nosniff"},
            )
        response = await call_next(request)
        response.headers["X-Content-Type-Options"] = "nosniff"
        response.headers["X-Frame-Options"] = "DENY"
        if request.url.path.startswith("/api/"):
            response.headers["Cache-Control"] = "no-store"
        return response
