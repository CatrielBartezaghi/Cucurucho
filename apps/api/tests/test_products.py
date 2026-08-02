from __future__ import annotations

import logging

from conftest import FakeImageStorage
from fastapi.testclient import TestClient

JPEG_IMAGE = b"\xff\xd8\xffimage"
PNG_IMAGE = b"\x89PNG\r\n\x1a\nimage"
WEBP_IMAGE = b"RIFF\x05\x00\x00\x00WEBPimage"


def test_product_can_be_edited_deactivated_and_reactivated(
    client: TestClient, login, product_factory
):
    login()
    product = product_factory("Palito", "500.00")

    updated = client.put(
        f"/api/productos/{product['id']}", json={"name": "Palito bombón", "price": "750.50"}
    )
    assert updated.status_code == 200
    assert updated.json()["price"] == "750.50"

    assert client.post(f"/api/productos/{product['id']}/inactivar").json()["active"] is False
    assert client.get("/api/productos").json() == []
    assert len(client.get("/api/productos?incluir_inactivos=true").json()) == 1
    assert client.post(f"/api/productos/{product['id']}/activar").json()["active"] is True


def test_product_image_can_be_replaced_and_removed(
    client: TestClient, login, product_factory, image_storage: FakeImageStorage
) -> None:
    login()
    product = product_factory("Torta helada", "10000.00")
    first = client.put(
        f"/api/productos/{product['id']}/imagen",
        files={"image": ("torta.png", PNG_IMAGE, "image/png")},
    )
    assert first.status_code == 200
    first_url = first.json()["image_url"]

    second = client.put(
        f"/api/productos/{product['id']}/imagen",
        files={"image": ("torta.webp", WEBP_IMAGE, "image/webp")},
    )
    assert second.status_code == 200
    assert second.json()["image_url"] != first_url
    assert image_storage.deleted == ["products/image-1"]

    removed = client.delete(f"/api/productos/{product['id']}/imagen")
    assert removed.json()["image_url"] is None
    assert image_storage.deleted[-1] == "products/image-2"


def test_invalid_or_failed_image_keeps_the_current_image(
    client: TestClient, login, product_factory, image_storage: FakeImageStorage
) -> None:
    login()
    product = product_factory("Cucurucho", "1000.00")
    uploaded = client.put(
        f"/api/productos/{product['id']}/imagen",
        files={"image": ("cono.jpg", JPEG_IMAGE, "image/jpeg")},
    ).json()

    invalid = client.put(
        f"/api/productos/{product['id']}/imagen",
        files={"image": ("cono.gif", b"invalid", "image/gif")},
    )
    assert invalid.status_code == 422

    image_storage.fail_upload = True
    failed = client.put(
        f"/api/productos/{product['id']}/imagen",
        files={"image": ("cono.png", PNG_IMAGE, "image/png")},
    )
    assert failed.status_code == 502
    catalog = client.get("/api/productos").json()
    assert catalog[0]["image_url"] == uploaded["image_url"]


def test_image_content_must_match_its_declared_format(
    client: TestClient, login, product_factory
) -> None:
    login()
    product = product_factory("Almendrado", "3500.00")

    disguised = client.put(
        f"/api/productos/{product['id']}/imagen",
        files={"image": ("almendrado.png", b"not really a png", "image/png")},
    )

    assert disguised.status_code == 422
    assert disguised.json()["code"] == "invalid_image_type"
    assert client.get("/api/productos").json()[0]["image_url"] is None


def test_failed_image_cleanup_keeps_the_new_reference_and_is_logged(
    client: TestClient,
    login,
    product_factory,
    image_storage: FakeImageStorage,
    caplog,
) -> None:
    login()
    product = product_factory("Bombón", "1800.00")
    client.put(
        f"/api/productos/{product['id']}/imagen",
        files={"image": ("bombon.jpg", JPEG_IMAGE, "image/jpeg")},
    )
    image_storage.fail_delete = True

    with caplog.at_level(logging.ERROR):
        replaced = client.put(
            f"/api/productos/{product['id']}/imagen",
            files={"image": ("bombon.png", PNG_IMAGE, "image/png")},
        )

    assert replaced.status_code == 200
    assert replaced.json()["image_url"].endswith("products/image-2")
    assert "products/image-1" in caplog.text


def test_image_larger_than_five_megabytes_is_rejected(
    client: TestClient, login, product_factory
) -> None:
    login()
    product = product_factory("Torta", "5000.00")
    response = client.put(
        f"/api/productos/{product['id']}/imagen",
        files={"image": ("large.png", b"x" * (5 * 1024 * 1024 + 1), "image/png")},
    )
    assert response.status_code == 422
    assert response.json()["code"] == "image_too_large"
