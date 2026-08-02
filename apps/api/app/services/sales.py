from __future__ import annotations

import hashlib
import json
import uuid
from collections.abc import Callable
from datetime import UTC, date, datetime
from decimal import Decimal
from zoneinfo import ZoneInfo

from sqlalchemy import select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session, selectinload

from ..errors import ApiError
from ..models import Product, Sale, SaleDetail
from ..schemas import SaleInput

BUENOS_AIRES = ZoneInfo("America/Argentina/Buenos_Aires")


class Sales:
    def __init__(self, clock: Callable[[], datetime] | None = None) -> None:
        self._clock = clock or (lambda: datetime.now(UTC))

    def confirm(
        self, db: Session, idempotency_key: str, data: SaleInput
    ) -> tuple[Sale, bool]:
        fingerprint = self._fingerprint(data)
        existing = self._by_idempotency_key(db, idempotency_key)
        if existing is not None:
            self._require_same_request(existing, fingerprint)
            return existing, False

        product_ids = {detail.product_id for detail in data.details}
        products = {
            product.id: product
            for product in db.scalars(
                select(Product).where(Product.id.in_(product_ids)).with_for_update()
            )
        }
        if any(
            detail.product_id not in products or not products[detail.product_id].active
            for detail in data.details
        ):
            raise ApiError(
                409,
                "product_unavailable",
                "Uno o más Productos ya no están disponibles.",
                {"details": "Actualizá la selección antes de confirmar."},
            )

        now = self._clock()
        if now.tzinfo is None:
            raise RuntimeError("El reloj de Ventas debe devolver un instante con zona horaria.")
        sale = Sale(
            idempotency_key=idempotency_key,
            request_fingerprint=fingerprint,
            payment_method=data.payment_method,
            total=Decimal("0.00"),
            sold_at=now,
            sale_day=now.astimezone(BUENOS_AIRES).date(),
        )
        for position, requested in enumerate(data.details):
            product = products[requested.product_id]
            sale.total += product.price * requested.quantity
            sale.details.append(
                SaleDetail(
                    product_id=product.id,
                    product_name=product.name,
                    unit_price=product.price,
                    quantity=requested.quantity,
                    position=position,
                )
            )
        db.add(sale)
        try:
            db.commit()
        except IntegrityError:
            db.rollback()
            existing = self._by_idempotency_key(db, idempotency_key)
            if existing is None:
                raise
            self._require_same_request(existing, fingerprint)
            return existing, False
        return sale, True

    def by_day(self, db: Session, day: date) -> tuple[list[Sale], Decimal]:
        sales = list(
            db.scalars(
                select(Sale)
                .options(selectinload(Sale.details))
                .where(Sale.sale_day == day)
                .order_by(Sale.sold_at.desc())
            )
        )
        total_sold = sum(
            (sale.total for sale in sales if sale.annulled_at is None), Decimal("0.00")
        )
        return sales, total_sold

    def get(self, db: Session, sale_id: uuid.UUID, for_update: bool = False) -> Sale:
        query = select(Sale).options(selectinload(Sale.details)).where(Sale.id == sale_id)
        if for_update:
            query = query.with_for_update()
        sale = db.scalar(query)
        if sale is None:
            raise ApiError(404, "sale_not_found", "No se encontró la Venta.")
        return sale

    def annul(self, db: Session, sale_id: uuid.UUID, reason: str) -> Sale:
        sale = self.get(db, sale_id, for_update=True)
        if sale.annulled_at is not None:
            raise ApiError(409, "sale_already_annulled", "La Venta ya fue anulada.")
        sale.annulment_reason = reason
        sale.annulled_at = self._clock()
        db.commit()
        return sale

    def replace_observation(self, db: Session, sale_id: uuid.UUID, observation: str) -> Sale:
        sale = self.get(db, sale_id, for_update=True)
        sale.observation = observation
        db.commit()
        return sale

    def remove_observation(self, db: Session, sale_id: uuid.UUID) -> Sale:
        sale = self.get(db, sale_id, for_update=True)
        sale.observation = None
        db.commit()
        return sale

    @staticmethod
    def _fingerprint(data: SaleInput) -> str:
        canonical = json.dumps(data.model_dump(mode="json"), sort_keys=True, separators=(",", ":"))
        return hashlib.sha256(canonical.encode("utf-8")).hexdigest()

    @staticmethod
    def _require_same_request(sale: Sale, fingerprint: str) -> None:
        if sale.request_fingerprint != fingerprint:
            raise ApiError(
                409,
                "idempotency_conflict",
                "La clave de confirmación ya se usó para otra Venta.",
            )

    @staticmethod
    def _by_idempotency_key(db: Session, key: str) -> Sale | None:
        return db.scalar(
            select(Sale)
            .options(selectinload(Sale.details))
            .where(Sale.idempotency_key == key)
        )

