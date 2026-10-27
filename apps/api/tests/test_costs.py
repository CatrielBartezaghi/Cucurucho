"""Costos históricos, validaciones de recetas y cobertura de rentabilidad."""

from __future__ import annotations

from fastapi.testclient import TestClient


def create_supply(client: TestClient, name: str, unit: str) -> dict[str, str]:
    response = client.post("/api/insumos", json={"name": name, "unit": unit})
    assert response.status_code == 201, response.text
    return response.json()


def buy(client: TestClient, supply_id: str, quantity: str, cost: str) -> None:
    response = client.post(
        "/api/compras-insumos",
        json={"supply_id": supply_id, "quantity": quantity, "total_cost": cost},
    )
    assert response.status_code == 201, response.text


def sale(client: TestClient, product_id: str, key: str, quantity: int = 1,
         weight: str | None = None) -> dict[str, object]:
    item: dict[str, object] = {"product_id": product_id, "quantity": quantity}
    if weight:
        item["weight_kg"] = weight
    response = client.post(
        "/api/ventas", headers={"Idempotency-Key": key},
        json={"payment_method": "cash", "details": [item]},
    )
    assert response.status_code == 201, response.text
    return response.json()


def metrics(client: TestClient, sale_day: str) -> dict[str, object]:
    result = client.get(f"/api/rentabilidad?desde={sale_day}&hasta={sale_day}")
    assert result.status_code == 200, result.text
    return result.json()


def test_supplies_purchases_and_cost_snapshots(client: TestClient, login, product_factory) -> None:
    login()
    product = product_factory("Kilo", "17000.00")
    ice = create_supply(client, "Helado", "kg")
    box = create_supply(client, "Pote térmico", "unit")
    assert client.post("/api/insumos", json={"name": " helado ", "unit": "kg"}).status_code == 409

    before = sale(client, product["id"], "costs-before")
    assert metrics(client, before["sale_day"])["missing_lines"] == 1

    buy(client, ice["id"], "2.000", "14000.00")
    buy(client, box["id"], "10.000", "5000.00")
    recipe = client.put(f"/api/productos/{product['id']}/receta", json={"items": [
        {"supply_id": ice["id"], "quantity": "1.000"},
        {"supply_id": box["id"], "quantity": "1.000"},
    ]})
    assert recipe.status_code == 200, recipe.text

    first = sale(client, product["id"], "costs-first", 2)
    assert first["total"] == "34000.00"
    report = metrics(client, first["sale_day"])
    assert report["known_cost"] == "15000.00"
    assert report["known_revenue"] == "34000.00"
    assert report["gross_profit"] == "19000.00"
    assert report["missing_lines"] == 1

    # A price change affects future sales only.
    buy(client, ice["id"], "2.000", "16000.00")
    second = sale(client, product["id"], "costs-second")
    after = metrics(client, second["sale_day"])
    assert after["known_cost"] == "23500.00"
    assert after["gross_profit"] == "27500.00"
    assert after["unknown_revenue"] == "17000.00"

    assert client.post(
        f"/api/ventas/{second['id']}/anulacion", json={"reason": "Corrección"}
    ).status_code == 200
    annulled = metrics(client, second["sale_day"])
    assert annulled["known_cost"] == "15000.00"

    purchases = client.get("/api/compras-insumos").json()
    assert len(purchases) == 3
    assert client.get("/api/insumos").json()[0]["current_unit_cost"] is not None


def test_weighted_recipe_variable_and_fixed(client: TestClient, login) -> None:
    login()
    category = next(c for c in client.get("/api/categorias").json() if c["name"] == "Helado")
    product = client.post("/api/productos", json={
        "name": "Torta", "price": "12000.00",
        "pricing_type": "weight", "category_id": category["id"],
    }).json()
    cream = create_supply(client, "Mezcla", "kg")
    package = create_supply(client, "Caja", "unit")
    buy(client, cream["id"], "1.000", "4000.00")
    buy(client, package["id"], "1.000", "200.00")
    assert client.put(f"/api/productos/{product['id']}/receta", json={"items": [
        {"supply_id": cream["id"], "quantity": "1.000", "mode": "variable"},
        {"supply_id": package["id"], "quantity": "1.000", "mode": "fixed"},
    ]}).status_code == 200
    created = sale(client, product["id"], "weighted-costs", weight="1.250")
    report = metrics(client, created["sale_day"])
    assert report["known_cost"] == "5200.00"
    assert report["gross_profit"] == "9800.00"


def test_incomplete_costs_invalid_input_and_auth(client: TestClient, login, product_factory) -> None:
    assert client.get("/api/insumos").status_code == 401
    login()
    product = product_factory("Vaso", "2000.00")
    cup = create_supply(client, "Vaso plástico", "unit")
    invalid = client.post("/api/compras-insumos", json={
        "supply_id": cup["id"], "quantity": "-1.000", "total_cost": "1500.00",
    })
    assert invalid.status_code == 422
    duplicates = client.put(f"/api/productos/{product['id']}/receta", json={"items": [
        {"supply_id": cup["id"], "quantity": "1.000"},
        {"supply_id": cup["id"], "quantity": "2.000"},
    ]})
    assert duplicates.status_code == 422
    assert client.put(f"/api/productos/{product['id']}/receta", json={"items": [
        {"supply_id": cup["id"], "quantity": "1.000"},
    ]}).status_code == 200
    unknown = sale(client, product["id"], "no-purchase")
    assert metrics(client, unknown["sale_day"])["unknown_revenue"] == "2000.00"
    assert client.get("/api/rentabilidad?desde=2026-02-02&hasta=2026-01-01").status_code == 422
