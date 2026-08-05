from __future__ import annotations

from starlette.types import ASGIApp, Receive, Scope, Send

from app.config import get_settings
from app.main import app as fastapi_app
from app.storage import bind_blob_oidc_credentials, reset_blob_oidc_credentials


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


app = BlobOidcMiddleware(fastapi_app)

__all__ = ["app"]
