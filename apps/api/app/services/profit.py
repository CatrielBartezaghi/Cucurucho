"""Rentabilidad bruta sobre costos históricos conocidos, excluyendo ventas anuladas."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import date
from decimal import Decimal

from sqlalchemy import select
from sqlalchemy.orm import Session

from ..errors import ApiError
from ..models import Sale, SaleDetail
from .costs import fmt


@dataclass
class ProductResults:
    product_id: str
    name: str
    revenue: Decimal = Decimal("0.00")
    known_revenue: Decimal = Decimal("0.00")
    known_cost: Decimal = Decimal("0.00")
    missing_lines: int = 0
    lines: int = 0

    def output(self) -> dict[str, object]:
        profit = self.known_revenue - self.known_cost
        return {
            "product_id": self.product_id,
            "name": self.name,
            "revenue": fmt(self.revenue),
            "known_revenue": fmt(self.known_revenue),
            "known_cost": fmt(self.known_cost),
            "gross_profit": fmt(profit),
            "gross_margin_pct": (
                fmt(profit * 100 / self.known_revenue) if self.known_revenue else None
            ),
            "missing_lines": self.missing_lines,
            "lines": self.lines,
        }


def report(db: Session, since: date, until: date) -> dict[str, object]:
    if until < since or (until - since).days > 365:
        raise ApiError(422, "invalid_period", "Elegí un período de hasta 366 días.")
    details = db.scalars(
        select(SaleDetail)
        .join(Sale, SaleDetail.sale_id == Sale.id)
        .where(
            Sale.sale_day >= since,
            Sale.sale_day <= until,
            Sale.annulled_at.is_(None),
        )
        .order_by(SaleDetail.product_name)
    )
    revenue = Decimal("0.00")
    known_revenue = Decimal("0.00")
    known_cost = Decimal("0.00")
    missing_lines = 0
    products: dict[str, ProductResults] = {}
    for line in details:
        key = str(line.product_id)
        if key not in products:
            products[key] = ProductResults(product_id=key, name=line.product_name)
        item = products[key]
        item.name = line.product_name
        item.revenue += line.line_total
        item.lines += 1
        revenue += line.line_total
        if line.cost_total is None:
            missing_lines += 1
            item.missing_lines += 1
        else:
            known_revenue += line.line_total
            known_cost += line.cost_total
            item.known_revenue += line.line_total
            item.known_cost += line.cost_total
    profit = known_revenue - known_cost
    return {
        "from": since.isoformat(),
        "to": until.isoformat(),
        "total_revenue": fmt(revenue),
        "known_revenue": fmt(known_revenue),
        "unknown_revenue": fmt(revenue - known_revenue),
        "known_cost": fmt(known_cost),
        "gross_profit": fmt(profit),
        "gross_margin_pct": fmt(profit * 100 / known_revenue) if known_revenue else None,
        "missing_lines": missing_lines,
        "products": [item.output() for item in products.values()],
    }
