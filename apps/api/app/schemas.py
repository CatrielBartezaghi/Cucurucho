from __future__ import annotations

import uuid
from datetime import date, datetime
from decimal import Decimal
from typing import Literal

from pydantic import BaseModel, ConfigDict, Field, field_validator

Money = Decimal
PaymentMethod = Literal["cash", "transfer", "debit_card", "credit_card", "qr"]


def validate_money(value: Decimal) -> Decimal:
    quantized = value.quantize(Decimal("0.01"))
    if value <= 0 or value != quantized:
        raise ValueError("Debe ser un importe positivo con hasta dos decimales.")
    return quantized


class LoginInput(BaseModel):
    username: str
    password: str


class ProductInput(BaseModel):
    name: str = Field(max_length=150)
    price: Decimal

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


class ProductOutput(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    name: str
    price: str
    active: bool
    image_url: str | None


class SaleDetailInput(BaseModel):
    product_id: uuid.UUID
    quantity: int = Field(gt=0)


class SaleInput(BaseModel):
    payment_method: PaymentMethod
    details: list[SaleDetailInput] = Field(min_length=1)


class ObservationInput(BaseModel):
    observation: str

    @field_validator("observation")
    @classmethod
    def valid_observation(cls, value: str) -> str:
        trimmed = value.strip()
        if not trimmed:
            raise ValueError("La observación no puede quedar vacía.")
        return trimmed


class AnnulmentInput(BaseModel):
    reason: str

    @field_validator("reason")
    @classmethod
    def valid_reason(cls, value: str) -> str:
        trimmed = value.strip()
        if not trimmed:
            raise ValueError("El motivo de anulación es obligatorio.")
        return trimmed


class AnnulmentOutput(BaseModel):
    reason: str
    annulled_at: datetime


class SaleDetailOutput(BaseModel):
    id: uuid.UUID
    product_id: uuid.UUID
    product_name: str
    unit_price: str
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
