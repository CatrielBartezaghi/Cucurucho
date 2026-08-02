from __future__ import annotations

import unicodedata
import uuid
from datetime import UTC, datetime

from sqlalchemy import select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from ..errors import ApiError
from ..models import Product
from ..schemas import ProductInput
from ..storage import ImageStorage

ALLOWED_IMAGE_TYPES = {"image/jpeg", "image/png", "image/webp"}
MAX_IMAGE_BYTES = 5 * 1024 * 1024


def normalized_product_name(name: str) -> str:
    decomposed = unicodedata.normalize("NFKD", name.strip().casefold())
    return "".join(character for character in decomposed if not unicodedata.combining(character))


class ProductCatalog:
    def __init__(self, image_storage: ImageStorage) -> None:
        self._images = image_storage

    def list(self, db: Session, include_inactive: bool) -> list[Product]:
        query = select(Product).order_by(Product.name)
        if not include_inactive:
            query = query.where(Product.active.is_(True))
        return list(db.scalars(query))

    def create(self, db: Session, data: ProductInput) -> Product:
        now = datetime.now(UTC)
        return self._persist(
            db,
            Product(
                name=data.name,
                normalized_name=normalized_product_name(data.name),
                price=data.price,
                active=True,
                created_at=now,
                updated_at=now,
            ),
        )

    def update(self, db: Session, product_id: uuid.UUID, data: ProductInput) -> Product:
        product = self.get(db, product_id)
        product.name = data.name
        product.normalized_name = normalized_product_name(data.name)
        product.price = data.price
        product.updated_at = datetime.now(UTC)
        return self._persist(db, product)

    def set_active(self, db: Session, product_id: uuid.UUID, active: bool) -> Product:
        product = self.get(db, product_id)
        product.active = active
        product.updated_at = datetime.now(UTC)
        db.commit()
        return product

    def replace_image(
        self,
        db: Session,
        product_id: uuid.UUID,
        content: bytes,
        content_type: str | None,
    ) -> Product:
        if content_type not in ALLOWED_IMAGE_TYPES:
            raise ApiError(
                422,
                "invalid_image_type",
                "La imagen debe ser JPEG, PNG o WebP.",
                {"image": "Elegí un archivo JPEG, PNG o WebP."},
            )
        if len(content) > MAX_IMAGE_BYTES:
            raise ApiError(
                422,
                "image_too_large",
                "La imagen no puede superar 5 MB.",
                {"image": "Elegí un archivo de hasta 5 MB."},
            )
        product = self.get(db, product_id)
        previous_key = product.image_key
        try:
            stored = self._images.upload(content, content_type)
        except Exception as exc:
            raise ApiError(
                502, "image_upload_failed", "No se pudo guardar la imagen. Reintentá."
            ) from exc
        product.image_key = stored.key
        product.image_url = stored.url
        product.updated_at = datetime.now(UTC)
        try:
            db.commit()
        except Exception:
            db.rollback()
            self._best_effort_delete(stored.key)
            raise
        if previous_key:
            self._best_effort_delete(previous_key)
        return product

    def remove_image(self, db: Session, product_id: uuid.UUID) -> Product:
        product = self.get(db, product_id)
        previous_key = product.image_key
        product.image_key = None
        product.image_url = None
        product.updated_at = datetime.now(UTC)
        db.commit()
        if previous_key:
            self._best_effort_delete(previous_key)
        return product

    def get(self, db: Session, product_id: uuid.UUID, for_update: bool = False) -> Product:
        query = select(Product).where(Product.id == product_id)
        if for_update:
            query = query.with_for_update()
        product = db.scalar(query)
        if product is None:
            raise ApiError(404, "product_not_found", "No se encontró el Producto.")
        return product

    @staticmethod
    def _persist(db: Session, product: Product) -> Product:
        try:
            db.add(product)
            db.commit()
        except IntegrityError as exc:
            db.rollback()
            raise ApiError(
                409,
                "product_name_conflict",
                "Ya existe un Producto con ese nombre.",
                {"name": "Elegí un nombre diferente."},
            ) from exc
        db.refresh(product)
        return product

    def _best_effort_delete(self, key: str) -> None:
        try:
            self._images.delete(key)
        except Exception:
            # A stale object is safe: PostgreSQL never points to a missing current image.
            pass

