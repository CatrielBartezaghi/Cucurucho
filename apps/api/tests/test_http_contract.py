from __future__ import annotations


def test_authenticated_catalog_and_sale_lifecycle(client, login, product_factory):
    login()
    quarter = product_factory("¼ kg", "4500.00")
    cone = product_factory("Cucurucho", "1200.50")

    created = client.post(
        "/api/ventas",
        headers={"Idempotency-Key": "sale-lifecycle-1"},
        json={
            "payment_method": "qr",
            "details": [
                {"product_id": quarter["id"], "quantity": 2},
                {"product_id": cone["id"], "quantity": 1},
                {"product_id": cone["id"], "quantity": 2},
            ],
        },
    )

    assert created.status_code == 201
    sale = created.json()
    assert sale["total"] == "12601.50"
    assert [detail["product_name"] for detail in sale["details"]] == [
        "¼ kg",
        "Cucurucho",
        "Cucurucho",
    ]

    repeated = client.post(
        "/api/ventas",
        headers={"Idempotency-Key": "sale-lifecycle-1"},
        json={
            "payment_method": "qr",
            "details": [
                {"product_id": quarter["id"], "quantity": 2},
                {"product_id": cone["id"], "quantity": 1},
                {"product_id": cone["id"], "quantity": 2},
            ],
        },
    )
    assert repeated.status_code == 200
    assert repeated.json() == sale

    listing = client.get(f"/api/ventas?dia={sale['sale_day']}")
    assert listing.status_code == 200
    assert listing.json()["total_sold"] == "12601.50"
    assert listing.json()["sales"][0]["id"] == sale["id"]

    observed = client.put(
        f"/api/ventas/{sale['id']}/observacion", json={"observation": "Cliente habitual"}
    )
    assert observed.status_code == 200
    assert observed.json()["observation"] == "Cliente habitual"

    annulled = client.post(
        f"/api/ventas/{sale['id']}/anulacion", json={"reason": "Carga duplicada"}
    )
    assert annulled.status_code == 200
    assert annulled.json()["annulment"]["reason"] == "Carga duplicada"

    after_annulment = client.get(f"/api/ventas?dia={sale['sale_day']}")
    assert after_annulment.json()["total_sold"] == "0.00"

    removed = client.delete(f"/api/ventas/{sale['id']}/observacion")
    assert removed.status_code == 200
    assert removed.json()["observation"] is None


def test_api_rejects_unauthenticated_access(client):
    response = client.get("/api/productos")
    assert response.status_code == 401
    assert response.json() == {
        "code": "session_required",
        "message": "Tu sesión venció o fue revocada. Iniciá sesión nuevamente.",
        "field_errors": {},
    }


def test_product_names_are_unicode_normalized_and_prices_are_exact(client, login, product_factory):
    login()
    product = product_factory("  Café helado  ", "10.10")
    duplicate = client.post(
        "/api/productos",
        json={
            "name": "CAFE HELADO",
            "price": "10.20",
            "category_id": product["category"]["id"],
        },
    )
    assert duplicate.status_code == 409
    assert duplicate.json()["code"] == "product_name_conflict"

    invalid = client.post(
        "/api/productos",
        json={
            "name": "Torta",
            "price": "1.001",
            "category_id": product["category"]["id"],
        },
    )
    assert invalid.status_code == 422
    assert invalid.json()["field_errors"]["price"]


def test_mutations_require_same_origin(client, login):
    login()
    response = client.post(
        "/api/productos",
        headers={"Origin": "https://evil.example"},
        json={"name": "Torta", "price": "10.00"},
    )
    assert response.status_code == 403
    assert response.json()["code"] == "invalid_origin"


def test_openapi_is_available_and_stable(client):
    schema = client.get("/api/openapi.json")
    assert schema.status_code == 200
    assert "/api/ventas" in schema.json()["paths"]
    assert "/api/productos" in schema.json()["paths"]
    validation_error = schema.json()["paths"]["/api/ventas"]["post"]["responses"]["422"]
    assert validation_error["content"]["application/json"]["schema"] == {
        "$ref": "#/components/schemas/ErrorOutput"
    }
