from __future__ import annotations

import base64

import requests

from app.config import get_settings
from app.main import app
from app.storage import VercelBlobStorage

__all__ = ["app"]


@app.get("/api/__blob-smoke-7f3e8c1a")
def blob_smoke_test() -> dict[str, object]:
    settings = get_settings()
    try:
        storage = VercelBlobStorage(settings)
        content = base64.b64decode(
            "iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAQAAAC1HAwCAAAAC0lEQVR42mNk+A8AAQUBAScY42YAAAAASUVORK5CYII="
        )
        stored = storage.upload(content, "image/png")
        try:
            response = requests.get(stored.url, timeout=10)
            response.raise_for_status()
            return {
                "status": "ok",
                "token_detected": True,
                "url_accessible": True,
                "content_type": response.headers.get("content-type"),
            }
        finally:
            storage.delete(stored.key)
    except Exception as exc:
        return {
            "status": "error",
            "token_detected": settings.blob_read_write_token is not None
            or settings.vercel_blob_read_write_token is not None,
            "error_type": type(exc).__name__,
            "message": str(exc),
        }
