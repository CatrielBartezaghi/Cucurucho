"""Catálogo de insumos, compras e insumos por producto."""

from __future__ import annotations

import uuid
from datetime import UTC, datetime
from decimal import ROUND_HALF_UP, Decimal

from sqlalchemy import select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session, selectinload

from ..errors import ApiError
from ..models import Product, ProductSupply, Supply, SupplyPurchase
from ..schemas import PurchaseInput, RecipeInput, SupplyInput, SupplyUpdate
from .catalog import normalized_name

CENT = Decimal("0.01")
FOUR = Decimal("0.0001")


def fmt(value: Decimal, places: int = 2) -> str:
    return f"{value:.{places}f}"


def supply_output(supply: Supply) -> dict[str, object]:
    return {
        "id": str(supply.id), "name": supply.name, "unit": supply.unit,
        "current_unit_cost": fmt(supply.current_unit_cost, 4)
        if supply.current_unit_cost is not None else None,
        "active": supply.active,
    }


def purchase_output(purchase: SupplyPurchase) -> dict[str, object]:
    return {
        "id": str(purchase.id), "supply_id": str(purchase.supply_id),
        "supply_name": purchase.supply.name, "quantity": fmt(purchase.quantity, 3),
        "total_cost": fmt(purchase.total_cost),
        "unit_cost": fmt(purchase.unit_cost, 4),
        "purchased_at": purchase.purchased_at.isoformat(),
    }


class Costs:
    def list_supplies(self, db: Session) -> list[dict[str, object]]:
        return [supply_output(item) for item in db.scalars(select(Supply).order_by(Supply.name))]

    def create_supply(self, db: Session, data: SupplyInput) -> dict[str, object]:
        now = datetime.now(UTC)
        supply = Supply(
            name=data.name, normalized_name=normalized_name(data.name),
            unit=data.unit, current_unit_cost=None, active=True,
            created_at=now, updated_at=now,
        )
        db.add(supply)
        try:
            db.commit()
        except IntegrityError as exc:
            db.rollback()
            raise ApiError(409, "supply_conflict", "Ya existe un insumo con ese nombre.") from exc
        return supply_output(supply)

    def update_supply(
        self, db: Session, supply_id: uuid.UUID, data: SupplyUpdate
    ) -> dict[str, object]:
        supply = self.get_supply(db, supply_id, lock=True)
        supply.name = data.name
        supply.normalized_name = normalized_name(data.name)
        supply.active = data.active
        supply.updated_at = datetime.now(UTC)
        try:
            db.commit()
        except IntegrityError as exc:
            db.rollback()
            raise ApiError(409, "supply_conflict", "Ya existe un insumo con ese nombre.") from exc
        return supply_output(supply)

    def get_supply(self, db: Session, supply_id: uuid.UUID, lock: bool = False) -> Supply:
        query = select(Supply).where(Supply.id == supply_id)
        if lock:
            query = query.with_for_update()
        supply = db.scalar(query)
        if supply is None:
            raise ApiError(404, "supply_not_found", "No se encontró el insumo.")
        return supply

    def add_purchase(self, db: Session, data: PurchaseInput) -> dict[str, object]:
        supply = self.get_supply(db, data.supply_id, lock=True)
        if not supply.active:
            raise ApiError(409, "inactive_supply", "El insumo está inactivo.")
        unit_cost = (data.total_cost / data.quantity).quantize(FOUR, rounding=ROUND_HALF_UP)
        purchase = SupplyPurchase(
            supply=supply, quantity=data.quantity, total_cost=data.total_cost,
            unit_cost=unit_cost, purchased_at=datetime.now(UTC),
        )
        supply.current_unit_cost = unit_cost
        supply.updated_at = purchase.purchased_at
        db.add(purchase)
        db.commit()
        return purchase_output(purchase)

    def list_purchases(self, db: Session) -> list[dict[str, object]]:
        purchases = db.scalars(
            select(SupplyPurchase).options(selectinload(SupplyPurchase.supply))
            .order_by(SupplyPurchase.purchased_at.desc()).limit(200)
        )
        return [purchase_output(item) for item in purchases]

    def recipe(self, db: Session, product_id: uuid.UUID) -> dict[str, object]:
        self.get_product(db, product_id)
        items = db.scalars(
            select(ProductSupply).options(selectinload(ProductSupply.supply))
            .where(ProductSupply.product_id == product_id)
            .order_by(ProductSupply.supply_id)
        )
        return {"product_id": str(product_id), "items": [
            {
                "supply_id": str(item.supply_id), "supply_name": item.supply.name,
                "unit": item.supply.unit, "quantity": fmt(item.quantity, 3),
                "mode": item.mode,
                "unit_cost": fmt(item.supply.current_unit_cost, 4)
                if item.supply.current_unit_cost is not None else None,
            }
            for item in items
        ]}

    def set_recipe(
        self, db: Session, product_id: uuid.UUID, data: RecipeInput
    ) -> dict[str, object]:
        self.get_product(db, product_id, lock=True)
        supply_ids = [item.supply_id for item in data.items]
        if len(set(supply_ids)) != len(supply_ids):
            raise ApiError(422, "duplicate_supply", "Un insumo no puede repetirse en la receta.")
        supplies = {
            supply.id: supply for supply in db.scalars(
                select(Supply).where(Supply.id.in_(supply_ids))
            )
        }
        if any(
            supply_id not in supplies or not supplies[supply_id].active
            for supply_id in supply_ids
        ):
            raise ApiError(422, "unknown_supply", "Revisá los insumos seleccionados.")
        for previous in db.scalars(
            select(ProductSupply).where(ProductSupply.product_id == product_id)
        ):
            db.delete(previous)
        db.flush()
        for item in data.items:
            db.add(ProductSupply(
                product_id=product_id, supply_id=item.supply_id,
                quantity=item.quantity, mode=item.mode,
            ))
        db.commit()
        return self.recipe(db, product_id)

    @staticmethod
    def get_product(db: Session, product_id: uuid.UUID, lock: bool = False) -> Product:
        query = select(Product).where(Product.id == product_id)
        if lock:
            query = query.with_for_update()
        product = db.scalar(query)
        if product is None:
            raise ApiError(404, "product_not_found", "No se encontró el producto.")
        return product

    @staticmethod
    def calculate_line_cost(
        db: Session, product_id: uuid.UUID, pricing_type: str,
        quantity: int, weight_kg: Decimal | None,
    ) -> Decimal | None:
        recipe = list(db.scalars(
            select(ProductSupply).options(selectinload(ProductSupply.supply))
            .where(ProductSupply.product_id == product_id)
        ))
        if not recipe or any(item.supply.current_unit_cost is None for item in recipe):
            return None
        total = Decimal("0")
        for item in recipe:
            # En productos por kg, variable escala con peso y fijo es por detalle.
            # En productos por unidad, cada insumo escala con la cantidad vendida.
            factor = (
                weight_kg if pricing_type == "weight" and item.mode == "variable"
                else Decimal("1") if pricing_type == "weight"
                else Decimal(quantity)
            )
            assert item.supply.current_unit_cost is not None
            total += item.supply.current_unit_cost * item.quantity * factor
        return total.quantize(CENT, rounding=ROUND_HALF_UP)
