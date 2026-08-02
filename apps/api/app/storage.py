from __future__ import annotations

import uuid
from dataclasses import dataclass
from typing import Protocol

import requests

from .config import Settings


@dataclass(frozen=True)
class StoredImage:
    key: str
    url: str


class ImageStorage(Protocol):
    def upload(self, content: bytes, content_type: str) -> StoredImage: ...

    def delete(self, key: str) -> None: ...


class VercelBlobStorage:
    def __init__(self, settings: Settings) -> None:
        token = settings.vercel_blob_read_write_token
        if token is None:
            raise RuntimeError("Falta VERCEL_BLOB_READ_WRITE_TOKEN para administrar imágenes.")
        self._token = token.get_secret_value()

    def upload(self, content: bytes, content_type: str) -> StoredImage:
        key = f"products/{uuid.uuid4()}"
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
        response = requests.delete(
            "https://blob.vercel-storage.com",
            json={"urls": [key]},
            headers={"Authorization": f"Bearer {self._token}"},
            timeout=30,
        )
        response.raise_for_status()


class UnconfiguredStorage:
    def upload(self, content: bytes, content_type: str) -> StoredImage:
        raise RuntimeError("El almacenamiento de imágenes no está configurado.")

    def delete(self, key: str) -> None:
        raise RuntimeError("El almacenamiento de imágenes no está configurado.")

