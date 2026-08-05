from __future__ import annotations

import base64

import requests
from starlette.types import ASGIApp, Receive, Scope, Send

from app.config import get_settings
from app.main import app as fastapi_app
from app.storage import (
    UnconfiguredStorage,
    bind_blob_oidc_credentials,
    reset_blob_oidc_credentials,
)


class BlobOidcMiddleware:
    def __init__(self, wrapped_app: ASGIApp) -> None:
        self._wrapped_app = wrapped_app

    async def __call__(self, scope: Scope, receive: Receive, send: Send) -> None:
        if scope["type"] != "http":
            await self._wrapped_app(scope, receive, send)
            return

        oidc_token = next(
            (
                value.decode("latin-1")
                for key, value in scope.get("headers", [])
                if key.lower() == b"x-vercel-oidc-token"
            ),
            None,
        )
        context_token = bind_blob_oidc_credentials(
            oidc_token,
            get_settings().blob_store_id,
        )
        try:
            await self._wrapped_app(scope, receive, send)
        finally:
            reset_blob_oidc_credentials(context_token)


@fastapi_app.get("/api/__blob-smoke-91c4d2ef")
def blob_smoke_test() -> dict[str, object]:
    try:
        storage = UnconfiguredStorage()
        content = base64.b64decode(
            "iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAQAAAC1HAwCAAAAC0lEQVR42mNk+A8AAQUBAScY42YAAAAASUVORK5CYII="
        )
        stored = storage.upload(content, "image/png")
        try:
            response = requests.get(stored.url, timeout=10)
            response.raise_for_status()
            return {
                "status": "ok",
                "url_accessible": True,
                "content_type": response.headers.get("content-type"),
            }
        finally:
            storage.delete(stored.key)
    except Exception as exc:
        return {
            "status": "error",
            "error_type": type(exc).__name__,
            "message": str(exc),
        }


app = BlobOidcMiddleware(fastapi_app)

__all__ = ["app"]
