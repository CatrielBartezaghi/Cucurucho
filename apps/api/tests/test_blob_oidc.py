from __future__ import annotations

from typing import Any

import pytest

from app.storage import (
    UnconfiguredStorage,
    VercelBlobStorage,
    bind_blob_oidc_credentials,
    reset_blob_oidc_credentials,
)


class FakeResponse:
    def __init__(self, payload: dict[str, str] | None = None) -> None:
        self._payload = payload or {}

    def raise_for_status(self) -> None:
        return None

    def json(self) -> dict[str, str]:
        return self._payload


def test_oidc_upload_uses_store_scoped_control_api(monkeypatch: pytest.MonkeyPatch) -> None:
    captured: dict[str, Any] = {}

    def fake_put(url: str, **kwargs: Any) -> FakeResponse:
        captured["url"] = url
        captured.update(kwargs)
        return FakeResponse(
            {
                "pathname": "products/image-random.png",
                "url": "https://store.public.blob.vercel-storage.com/products/image-random.png",
            }
        )

    monkeypatch.setattr("app.storage.requests.put", fake_put)

    storage = VercelBlobStorage(oidc_token="oidc-token", store_id="store_AbC123")
    stored = storage.upload(b"png", "image/png")

    assert captured["url"] == "https://vercel.com/api/blob/"
    assert captured["params"]["pathname"].startswith("products/")
    assert captured["headers"]["Authorization"] == "Bearer oidc-token"
    assert captured["headers"]["x-vercel-blob-store-id"] == "AbC123"
    assert captured["headers"]["x-api-version"] == "12"
    assert captured["headers"]["x-vercel-blob-access"] == "public"
    assert captured["headers"]["x-content-type"] == "image/png"
    assert stored.key == "products/image-random.png"


def test_oidc_delete_uses_blob_delete_endpoint(monkeypatch: pytest.MonkeyPatch) -> None:
    captured: dict[str, Any] = {}

    def fake_post(url: str, **kwargs: Any) -> FakeResponse:
        captured["url"] = url
        captured.update(kwargs)
        return FakeResponse()

    monkeypatch.setattr("app.storage.requests.post", fake_post)

    storage = VercelBlobStorage(oidc_token="oidc-token", store_id="store_AbC123")
    storage.delete("products/image.png")

    assert captured["url"] == "https://vercel.com/api/blob/delete"
    assert captured["json"] == {"urls": ["products/image.png"]}
    assert captured["headers"]["Authorization"] == "Bearer oidc-token"
    assert captured["headers"]["x-vercel-blob-store-id"] == "AbC123"


def test_unconfigured_storage_uses_request_bound_oidc_credentials(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setattr(
        "app.storage.requests.put",
        lambda *args, **kwargs: FakeResponse(
            {
                "pathname": "products/image.png",
                "url": "https://store.public.blob.vercel-storage.com/products/image.png",
            }
        ),
    )
    context_token = bind_blob_oidc_credentials("oidc-token", "store_AbC123")
    try:
        stored = UnconfiguredStorage().upload(b"png", "image/png")
    finally:
        reset_blob_oidc_credentials(context_token)

    assert stored.key == "products/image.png"


def test_unconfigured_storage_still_fails_without_credentials() -> None:
    with pytest.raises(RuntimeError, match="no está configurado"):
        UnconfiguredStorage().upload(b"png", "image/png")
