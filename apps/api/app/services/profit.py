"""Rentabilidad bruta sobre costos históricos conocidos, excluyendo ventas anuladas."""

from __future__ import annotations

from datetime import date
from decimal import Decimal

from sqlalchemy import select
from sqlalchemy.orm import Session

from ..errors import ApiError
from ..models import Sale, SaleDetail
from .costs import fmt


def report(db: Session, since: date, until: date) -> dict[str, object]:
    if until < since or (until - since).days > 365:
        raise ApiError(422, "invalid_period", "Elegí un período de hasta 366 días.")
    details = db.scalars(
        select(SaleDetail)
        .join(Sale, SaleDetail.sale_id == Sale.id)
        .where(
            Sale.sale_day >= since, Sale.sale_day <= until,
            Sale.annulled_at.is_(None),
        ).order_by(SaleDetail.product_name)
    )
    revenue = Decimal("0.00")
    known_revenue = Decimal("0.00")
    known_cost = Decimal("0.00")
    missing_lines = 0
    products: dict[str, dict[str, object]] = {}
    for line in details:
        key = str(line.product_id)
        if key not in products:
            products[key] = {
                "product_id": key, "name": line.product_name, "revenue": Decimal("0"),
                "known_revenue": Decimal("0"), "known_cost": Decimal("0"),
                "missing_lines": 0, "lines": 0,
            }
        item = products[key]
        item["name"] = line.product_name
        item["revenue"] += line.line_total
        item["lines"] += 1
        revenue += line.line_total
        if line.cost_total is None:
            missing_lines += 1
            item["missing_lines"] += 1
        else:
            known_revenue += line.line_total
            known_cost += line.cost_total
            item["known_revenue"] += line.line_total
            item["known_cost"] += line.cost_total

    def present(item: dict[str, object]) -> dict[str, object]:
        billed = item["known_revenue"]
        costs = item["known_cost"]
        profit = billed - costs
        return {
            "product_id": item["product_id"], "name": item["name"],
            "revenue": fmt(item["revenue"]),
            "known_revenue": fmt(billed), "known_cost": fmt(costs),
            "gross_profit": fmt(profit),
            "gross_margin_pct": fmt(profit * 100 / billed) if billed else None,
            "missing_lines": item["missing_lines"], "lines": item["lines"],
        }

    profit = known_revenue - known_cost
    return {
        "from": since.isoformat(), "to": until.isoformat(),
        "total_revenue": fmt(revenue),
        "known_revenue": fmt(known_revenue),
        "unknown_revenue": fmt(revenue - known_revenue),
        "known_cost": fmt(known_cost),
        "gross_profit": fmt(profit),
        "gross_margin_pct": fmt(profit * 100 / known_revenue) if known_revenue else None,
        "missing_lines": missing_lines,
        "products": [present(item) for item in products.values()],
    }
