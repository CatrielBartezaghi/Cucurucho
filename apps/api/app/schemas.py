from __future__ import annotations

import uuid
from datetime import date, datetime
from decimal import Decimal
from typing import Literal

from pydantic import BaseModel, ConfigDict, Field, field_validator

Money = Decimal
PaymentMethod = Literal["cash", "transfer", "debit_card", "credit_card", "qr"]


def validate_money(value: Decimal) -> Decimal:
    if not value.is_finite() or value <= 0 or value >= Decimal("10000000000"):
        raise ValueError("Debe ser un importe positivo con hasta dos decimales.")
    quantized = value.quantize(Decimal("0.01"))
    if value != quantized:
        raise ValueError("Debe ser un importe positivo con hasta dos decimales.")
    return quantized


def validate_non_empty_text(value: str, message: str) -> str:
    trimmed = value.strip()
    if not trimmed:
        raise ValueError(message)
    return trimmed


class LoginInput(BaseModel):
    username: str
    password: str


class ErrorOutput(BaseModel):
    code: str
    message: str
    field_errors: dict[str, str]


class CurrentSessionOutput(BaseModel):
    id: uuid.UUID
    username: str


class ProductInput(BaseModel):
    name: str = Field(max_length=150)
    price: Decimal
    category_id: uuid.UUID
    pricing_type: str = "unit"

    @field_validator("name")
    @classmethod
    def valid_name(cls, value: str) -> str:
        trimmed = value.strip()
        if not trimmed:
            raise ValueError("El nombre es obligatorio.")
        return trimmed

    @field_validator("price")
    @classmethod
    def valid_price(cls, value: Decimal) -> Decimal:
        return validate_money(value)


    @field_validator("pricing_type")
    @classmethod
    def valid_pricing_type(cls, value: str) -> str:
        if value not in {"unit", "weight"}:
            raise ValueError("El tipo de precio debe ser por unidad o por kilo.")
        return value


class CategoryInput(BaseModel):
    name: str = Field(max_length=100)

    @field_validator("name")
    @classmethod
    def valid_name(cls, value: str) -> str:
        return validate_non_empty_text(value, "El nombre de la Categoría es obligatorio.")


class CategoryOutput(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    name: str


class ProductOutput(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    name: str
    price: str
    pricing_type: str
    active: bool
    image_url: str | None
    category: CategoryOutput


class SaleDetailInput(BaseModel):
    product_id: uuid.UUID
    quantity: int = Field(gt=0)
    weight_kg: Decimal | None = None
    amount: Decimal | None = None

    @field_validator("weight_kg")
    @classmethod
    def valid_weight(cls, value: Decimal | None) -> Decimal | None:
        if value is None:
            return None
        if not value.is_finite() or value <= 0 or value != value.quantize(Decimal("0.001")):
            raise ValueError("El peso debe ser positivo y tener hasta tres decimales.")
        return value

    @field_validator("amount")
    @classmethod
    def valid_amount(cls, value: Decimal | None) -> Decimal | None:
        if value is None:
            return None
        return validate_money(value)


class SaleInput(BaseModel):
    payment_method: PaymentMethod
    details: list[SaleDetailInput] = Field(min_length=1)


class ObservationInput(BaseModel):
    observation: str

    @field_validator("observation")
    @classmethod
    def valid_observation(cls, value: str) -> str:
        return validate_non_empty_text(value, "La observación no puede quedar vacía.")


class AnnulmentInput(BaseModel):
    reason: str

    @field_validator("reason")
    @classmethod
    def valid_reason(cls, value: str) -> str:
        return validate_non_empty_text(value, "El motivo de anulación es obligatorio.")


class AnnulmentOutput(BaseModel):
    reason: str
    annulled_at: datetime


class SaleDetailOutput(BaseModel):
    id: uuid.UUID
    product_id: uuid.UUID
    product_name: str
    unit_price: str
    pricing_type: str
    weight_kg: str | None
    entry_method: str | None
    line_total: str
    quantity: int
    position: int


class SaleOutput(BaseModel):
    id: uuid.UUID
    payment_method: PaymentMethod
    total: str
    sold_at: datetime
    sale_day: date
    observation: str | None
    annulment: AnnulmentOutput | None
    details: list[SaleDetailOutput]


class SalesByDayOutput(BaseModel):
    day: date
    total_sold: str
    sales: list[SaleOutput]



class SupplyInput(BaseModel):
    name: str = Field(max_length=150)
    unit: Literal["kg", "unit"]

    @field_validator("name")
    @classmethod
    def valid_name(cls, value: str) -> str:
        return validate_non_empty_text(value, "El nombre del insumo es obligatorio.")


class SupplyUpdate(BaseModel):
    name: str = Field(max_length=150)
    active: bool

    @field_validator("name")
    @classmethod
    def valid_name(cls, value: str) -> str:
        return validate_non_empty_text(value, "El nombre del insumo es obligatorio.")


class PurchaseInput(BaseModel):
    supply_id: uuid.UUID
    quantity: Decimal
    total_cost: Decimal

    @field_validator("quantity")
    @classmethod
    def valid_quantity(cls, value: Decimal) -> Decimal:
        if (
            not value.is_finite()
            or value <= 0
            or value >= Decimal("1000000000")
            or value != value.quantize(Decimal("0.001"))
        ):
            raise ValueError("La cantidad debe ser positiva, con hasta tres decimales.")
        return value

    @field_validator("total_cost")
    @classmethod
    def valid_total(cls, value: Decimal) -> Decimal:
        if (
            not value.is_finite()
            or value < 0
            or value >= Decimal("10000000000")
            or value != value.quantize(Decimal("0.01"))
        ):
            raise ValueError("El importe debe ser no negativo y tener hasta dos decimales.")
        return value


class RecipeItemInput(BaseModel):
    supply_id: uuid.UUID
    quantity: Decimal
    mode: Literal["variable", "fixed"] = "variable"

    @field_validator("quantity")
    @classmethod
    def valid_quantity(cls, value: Decimal) -> Decimal:
        if (
            not value.is_finite()
            or value <= 0
            or value >= Decimal("1000000000")
            or value != value.quantize(Decimal("0.001"))
        ):
            raise ValueError(
                "La cantidad de la receta debe ser positiva y tener hasta tres decimales."
            )
        return value


class RecipeInput(BaseModel):
    items: list[RecipeItemInput] = Field(max_length=200)
