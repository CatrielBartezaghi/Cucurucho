from __future__ import annotations

from concurrent.futures import ThreadPoolExecutor
from datetime import UTC, datetime

from conftest import FakeImageStorage
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session, sessionmaker

from app.config import Settings
from app.main import create_app


def sale_payload(product_id: str, quantity: int = 1) -> dict[str, object]:
    return {
        "payment_method": "cash",
        "details": [{"product_id": product_id, "quantity": quantity}],
    }


def test_idempotency_key_rejects_different_content(client: TestClient, login, product_factory):
    login()
    product = product_factory("Medio kilo", "8000.00")
    assert client.post(
        "/api/ventas",
        headers={"Idempotency-Key": "same-key"},
        json=sale_payload(str(product["id"])),
    ).status_code == 201

    conflict = client.post(
        "/api/ventas",
        headers={"Idempotency-Key": "same-key"},
        json=sale_payload(str(product["id"]), 2),
    )
    assert conflict.status_code == 409
    assert conflict.json()["code"] == "idempotency_conflict"


def test_inactive_product_rolls_back_the_whole_sale(client: TestClient, login, product_factory):
    login()
    active = product_factory("Cucurucho", "1000.00")
    inactive = product_factory("Palito", "500.00")
    client.post(f"/api/productos/{inactive['id']}/inactivar")

    rejected = client.post(
        "/api/ventas",
        headers={"Idempotency-Key": "unavailable"},
        json={
            "payment_method": "transfer",
            "details": [
                {"product_id": active["id"], "quantity": 1},
                {"product_id": inactive["id"], "quantity": 1},
            ],
        },
    )
    assert rejected.status_code == 409
    assert rejected.json()["code"] == "product_unavailable"


def test_sale_keeps_historical_name_and_price(client: TestClient, login, product_factory):
    login()
    product = product_factory("Cuarto", "4500.00")
    sale = client.post(
        "/api/ventas",
        headers={"Idempotency-Key": "snapshot"},
        json=sale_payload(str(product["id"])),
    ).json()
    client.put(
        f"/api/productos/{product['id']}",
        json={"name": "Cuarto premium", "price": "5000.00"},
    )

    stored = client.get(f"/api/ventas/{sale['id']}").json()
    assert stored["details"][0]["product_name"] == "Cuarto"
    assert stored["details"][0]["unit_price"] == "4500.00"


def test_annulment_is_once_only_and_observation_remains_editable(
    client: TestClient, login, product_factory
):
    login()
    product = product_factory("Kilo", "15000.00")
    sale = client.post(
        "/api/ventas",
        headers={"Idempotency-Key": "annul-once"},
        json=sale_payload(str(product["id"])),
    ).json()

    assert client.post(
        f"/api/ventas/{sale['id']}/anulacion", json={"reason": " Error de carga "}
    ).status_code == 200
    repeated = client.post(
        f"/api/ventas/{sale['id']}/anulacion", json={"reason": "Otro motivo"}
    )
    assert repeated.status_code == 409

    observed = client.put(
        f"/api/ventas/{sale['id']}/observacion", json={"observation": " Se avisó al cliente "}
    )
    assert observed.status_code == 200
    assert observed.json()["observation"] == "Se avisó al cliente"
    assert observed.json()["annulment"]["reason"] == "Error de carga"


def test_concurrent_retries_create_only_one_sale(
    client: TestClient, login, product_factory
) -> None:
    login()
    product = product_factory("Cuarto", "4500.00")
    payload = sale_payload(str(product["id"]))

    def confirm() -> tuple[int, str]:
        with TestClient(
            client.app,
            base_url="https://testserver",
            headers={"Origin": "https://testserver"},
            cookies=client.cookies,
        ) as concurrent_client:
            response = concurrent_client.post(
                "/api/ventas",
                headers={"Idempotency-Key": "concurrent-retry"},
                json=payload,
            )
            return response.status_code, response.json()["id"]

    with ThreadPoolExecutor(max_workers=2) as executor:
        results = list(executor.map(lambda _index: confirm(), range(2)))

    assert {status for status, _sale_id in results} == {200, 201}
    assert len({sale_id for _status, sale_id in results}) == 1


def test_sale_day_uses_buenos_aires_at_both_sides_of_utc_midnight(
    settings: Settings,
    session_factory: sessionmaker[Session],
    image_storage: FakeImageStorage,
) -> None:
    moments = iter(
        [
            datetime(2026, 8, 2, 2, 30, tzinfo=UTC),
            datetime(2026, 8, 2, 3, 30, tzinfo=UTC),
        ]
    )
    app = create_app(settings, session_factory, image_storage, clock=lambda: next(moments))
    with TestClient(
        app,
        base_url="https://testserver",
        headers={"Origin": "https://testserver"},
    ) as fixed_client:
        assert fixed_client.post(
            "/api/sesion/login",
            json={"username": "operadora", "password": "helado-seguro"},
        ).status_code == 204
        product = fixed_client.post(
            "/api/productos", json={"name": "Kilo", "price": "15000.00"}
        ).json()
        first = fixed_client.post(
            "/api/ventas",
            headers={"Idempotency-Key": "before-midnight"},
            json=sale_payload(product["id"]),
        ).json()
        second = fixed_client.post(
            "/api/ventas",
            headers={"Idempotency-Key": "after-midnight"},
            json=sale_payload(product["id"]),
        ).json()

        assert first["sale_day"] == "2026-08-01"
        assert second["sale_day"] == "2026-08-02"
        assert len(fixed_client.get("/api/ventas?dia=2026-08-01").json()["sales"]) == 1
        assert len(fixed_client.get("/api/ventas?dia=2026-08-02").json()["sales"]) == 1
