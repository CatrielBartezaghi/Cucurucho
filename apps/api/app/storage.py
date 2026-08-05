from __future__ import annotations

import time
import uuid
from contextvars import ContextVar, Token
from dataclasses import dataclass
from typing import Protocol

import requests

from .config import Settings

BLOB_CONTROL_API = "https://vercel.com/api/blob"
BLOB_API_VERSION = "12"


@dataclass(frozen=True)
class StoredImage:
    key: str
    url: str


@dataclass(frozen=True)
class BlobOidcCredentials:
    token: str
    store_id: str


_oidc_credentials: ContextVar[BlobOidcCredentials | None] = ContextVar(
    "blob_oidc_credentials", default=None
)


def bind_blob_oidc_credentials(
    token: str | None, store_id: str | None
) -> Token[BlobOidcCredentials | None]:
    normalized_token = token.strip() if token else ""
    normalized_store_id = _normalize_store_id(store_id) if store_id else ""
    credentials = (
        BlobOidcCredentials(normalized_token, normalized_store_id)
        if normalized_token and normalized_store_id
        else None
    )
    return _oidc_credentials.set(credentials)


def reset_blob_oidc_credentials(context_token: Token[BlobOidcCredentials | None]) -> None:
    _oidc_credentials.reset(context_token)


def _normalize_store_id(store_id: str) -> str:
    normalized = store_id.strip()
    return normalized.removeprefix("store_")


class ImageStorage(Protocol):
    def upload(self, content: bytes, content_type: str) -> StoredImage: ...

    def delete(self, key: str) -> None: ...


class VercelBlobStorage:
    def __init__(
        self,
        settings: Settings | None = None,
        *,
        oidc_token: str | None = None,
        store_id: str | None = None,
    ) -> None:
        self._token: str
        self._store_id: str | None
        self._uses_oidc: bool

        normalized_oidc_token = oidc_token.strip() if oidc_token else ""
        normalized_store_id = _normalize_store_id(store_id) if store_id else ""
        if normalized_oidc_token and normalized_store_id:
            self._token = normalized_oidc_token
            self._store_id = normalized_store_id
            self._uses_oidc = True
            return

        static_token = settings.vercel_blob_read_write_token if settings else None
        if static_token is None:
            raise RuntimeError(
                "Faltan credenciales de Vercel Blob para administrar imágenes."
            )
        self._token = static_token.get_secret_value()
        self._store_id = None
        self._uses_oidc = False

    def upload(self, content: bytes, content_type: str) -> StoredImage:
        key = f"products/{uuid.uuid4()}"
        if self._uses_oidc:
            response = requests.put(
                f"{BLOB_CONTROL_API}/",
                params={"pathname": key},
                data=content,
                headers={
                    **self._oidc_headers(),
                    "x-vercel-blob-access": "public",
                    "x-content-type": content_type,
                    "x-add-random-suffix": "1",
                },
                timeout=30,
            )
        else:
            response = requests.put(
                f"https://blob.vercel-storage.com/{key}",
                data=content,
                headers={
                    "Authorization": f"Bearer {self._token}",
                    "Content-Type": content_type,
                    "x-add-random-suffix": "1",
                },
                timeout=30,
            )
        response.raise_for_status()
        payload = response.json()
        return StoredImage(key=payload["pathname"], url=payload["url"])

    def delete(self, key: str) -> None:
        if self._uses_oidc:
            response = requests.post(
                f"{BLOB_CONTROL_API}/delete",
                json={"urls": [key]},
                headers=self._oidc_headers(),
                timeout=30,
            )
        else:
            response = requests.delete(
                "https://blob.vercel-storage.com",
                json={"urls": [key]},
                headers={"Authorization": f"Bearer {self._token}"},
                timeout=30,
            )
        response.raise_for_status()

    def _oidc_headers(self) -> dict[str, str]:
        if self._store_id is None:
            raise RuntimeError("Falta BLOB_STORE_ID para autenticar Vercel Blob con OIDC.")
        request_id = f"{self._store_id}:{int(time.time() * 1000)}:{uuid.uuid4().hex}"
        return {
            "Authorization": f"Bearer {self._token}",
            "x-vercel-blob-store-id": self._store_id,
            "x-api-blob-request-id": request_id,
            "x-api-blob-request-attempt": "0",
            "x-api-version": BLOB_API_VERSION,
        }


class UnconfiguredStorage:
    def upload(self, content: bytes, content_type: str) -> StoredImage:
        return self._runtime_storage().upload(content, content_type)

    def delete(self, key: str) -> None:
        self._runtime_storage().delete(key)

    @staticmethod
    def _runtime_storage() -> VercelBlobStorage:
        credentials = _oidc_credentials.get()
        if credentials is None:
            raise RuntimeError("El almacenamiento de imágenes no está configurado.")
        return VercelBlobStorage(
            oidc_token=credentials.token,
            store_id=credentials.store_id,
        )
