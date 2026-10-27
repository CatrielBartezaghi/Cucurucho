from __future__ import annotations

import uuid
from datetime import date, datetime
from decimal import Decimal

from sqlalchemy import (
    Boolean,
    CheckConstraint,
    Date,
    DateTime,
    ForeignKey,
    Integer,
    Numeric,
    String,
    Text,
    UniqueConstraint,
)
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from .db import Base


class User(Base):
    __tablename__ = "users"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    username: Mapped[str] = mapped_column(String(100), unique=True)
    password_hash: Mapped[str] = mapped_column(Text)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True))


class BrowserSession(Base):
    __tablename__ = "browser_sessions"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"))
    token_hash: Mapped[str] = mapped_column(String(64), unique=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True))
    expires_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), index=True)
    user: Mapped[User] = relationship()


class Category(Base):
    __tablename__ = "categories"
    __table_args__ = (UniqueConstraint("normalized_name", name="uq_categories_normalized_name"),)

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    name: Mapped[str] = mapped_column(String(100))
    normalized_name: Mapped[str] = mapped_column(String(100))
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True))
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True))


class Product(Base):
    __tablename__ = "products"
    __table_args__ = (
        CheckConstraint("price > 0", name="ck_products_positive_price"),
        CheckConstraint("pricing_type IN ('unit','weight')", name="ck_products_pricing_type"),
        UniqueConstraint("normalized_name", name="uq_products_normalized_name"),
    )

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    category_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("categories.id", ondelete="RESTRICT"), index=True
    )
    name: Mapped[str] = mapped_column(String(150))
    normalized_name: Mapped[str] = mapped_column(String(150))
    price: Mapped[Decimal] = mapped_column(Numeric(12, 2))
    pricing_type: Mapped[str] = mapped_column(String(10), default="unit", server_default="unit")
    active: Mapped[bool] = mapped_column(Boolean, default=True)
    image_key: Mapped[str | None] = mapped_column(String(500), nullable=True)
    image_url: Mapped[str | None] = mapped_column(Text, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True))
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True))
    category: Mapped[Category] = relationship()


class Sale(Base):
    __tablename__ = "sales"
    __table_args__ = (
        CheckConstraint("total >= 0", name="ck_sales_nonnegative_total"),
        CheckConstraint(
            "payment_method IN ('cash','transfer','debit_card','credit_card','qr')",
            name="ck_sales_payment_method",
        ),
        UniqueConstraint("idempotency_key", name="uq_sales_idempotency_key"),
    )

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    idempotency_key: Mapped[str] = mapped_column(String(200))
    request_fingerprint: Mapped[str] = mapped_column(String(64))
    payment_method: Mapped[str] = mapped_column(String(30))
    total: Mapped[Decimal] = mapped_column(Numeric(14, 2))
    sold_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), index=True)
    sale_day: Mapped[date] = mapped_column(Date, index=True)
    observation: Mapped[str | None] = mapped_column(Text, nullable=True)
    annulment_reason: Mapped[str | None] = mapped_column(Text, nullable=True)
    annulled_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    details: Mapped[list[SaleDetail]] = relationship(
        back_populates="sale", cascade="all, delete-orphan", order_by="SaleDetail.position"
    )


class SaleDetail(Base):
    __tablename__ = "sale_details"
    __table_args__ = (
        CheckConstraint("quantity > 0", name="ck_sale_details_positive_quantity"),
        CheckConstraint("unit_price > 0", name="ck_sale_details_positive_price"),
        CheckConstraint("pricing_type IN ('unit','weight')", name="ck_sale_details_pricing_type"),
        CheckConstraint("line_total > 0", name="ck_sale_details_positive_line_total"),
        CheckConstraint(
            "weight_kg IS NULL OR weight_kg > 0", name="ck_sale_details_positive_weight"
        ),
        CheckConstraint(
            "(pricing_type = 'unit' AND weight_kg IS NULL AND entry_method IS NULL) OR "
            "(pricing_type = 'weight' AND weight_kg IS NOT NULL AND "
            "entry_method IN ('weight','amount') AND quantity = 1)",
            name="ck_sale_details_pricing_consistency",
        ),
        UniqueConstraint("sale_id", "position", name="uq_sale_details_position"),
    )

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    sale_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("sales.id", ondelete="RESTRICT"))
    product_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("products.id", ondelete="RESTRICT"))
    product_name: Mapped[str] = mapped_column(String(150))
    unit_price: Mapped[Decimal] = mapped_column(Numeric(12, 2))
    pricing_type: Mapped[str] = mapped_column(String(10), default="unit", server_default="unit")
    weight_kg: Mapped[Decimal | None] = mapped_column(Numeric(12, 3), nullable=True)
    entry_method: Mapped[str | None] = mapped_column(String(10), nullable=True)
    line_total: Mapped[Decimal] = mapped_column(Numeric(14, 2))
    quantity: Mapped[int] = mapped_column(Integer)
    position: Mapped[int] = mapped_column(Integer)
    cost_total: Mapped[Decimal | None] = mapped_column(Numeric(14, 2), nullable=True)
    sale: Mapped[Sale] = relationship(back_populates="details")



class Supply(Base):
    __tablename__ = "supplies"
    __table_args__ = (
        UniqueConstraint("normalized_name", name="uq_supplies_normalized_name"),
        CheckConstraint("unit IN ('kg','unit')", name="ck_supplies_unit"),
        CheckConstraint(
            "current_unit_cost IS NULL OR current_unit_cost >= 0", name="ck_supplies_cost"
        ),
    )

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    name: Mapped[str] = mapped_column(String(150))
    normalized_name: Mapped[str] = mapped_column(String(150))
    unit: Mapped[str] = mapped_column(String(10))
    current_unit_cost: Mapped[Decimal | None] = mapped_column(Numeric(14, 4), nullable=True)
    active: Mapped[bool] = mapped_column(Boolean, default=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True))
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True))


class SupplyPurchase(Base):
    __tablename__ = "supply_purchases"
    __table_args__ = (
        CheckConstraint("quantity > 0", name="ck_supply_purchases_quantity"),
        CheckConstraint("total_cost >= 0", name="ck_supply_purchases_total_cost"),
        CheckConstraint("unit_cost >= 0", name="ck_supply_purchases_unit_cost"),
    )

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    supply_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("supplies.id", ondelete="RESTRICT"), index=True
    )
    quantity: Mapped[Decimal] = mapped_column(Numeric(12, 3))
    total_cost: Mapped[Decimal] = mapped_column(Numeric(14, 2))
    unit_cost: Mapped[Decimal] = mapped_column(Numeric(14, 4))
    purchased_at: Mapped[datetime] = mapped_column(DateTime(timezone=True))
    supply: Mapped[Supply] = relationship()


class ProductSupply(Base):
    __tablename__ = "product_supplies"
    __table_args__ = (
        CheckConstraint("quantity > 0", name="ck_product_supplies_quantity"),
        CheckConstraint("mode IN ('variable','fixed')", name="ck_product_supplies_mode"),
    )

    product_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("products.id", ondelete="CASCADE"), primary_key=True
    )
    supply_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("supplies.id", ondelete="RESTRICT"), primary_key=True
    )
    quantity: Mapped[Decimal] = mapped_column(Numeric(12, 3))
    mode: Mapped[str] = mapped_column(String(10), default="variable")
    supply: Mapped[Supply] = relationship()
