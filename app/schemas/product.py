from datetime import datetime
from decimal import Decimal

from pydantic import BaseModel, ConfigDict, Field, field_validator


class ProductBase(BaseModel):
    sku: str = Field(min_length=1, max_length=64)
    name: str = Field(min_length=1, max_length=255)
    description: str | None = None
    price: Decimal = Field(ge=0, max_digits=10, decimal_places=2)
    low_stock_threshold: int = Field(default=10, ge=0)


class ProductCreate(ProductBase):
    stock_quantity: int = Field(default=0, ge=0)


class ProductUpdate(BaseModel):
    """Partial update. Stock is changed through the stock endpoint instead."""

    name: str | None = Field(default=None, min_length=1, max_length=255)
    description: str | None = None
    price: Decimal | None = Field(default=None, ge=0, max_digits=10, decimal_places=2)
    low_stock_threshold: int | None = Field(default=None, ge=0)


class ProductRead(ProductBase):
    model_config = ConfigDict(from_attributes=True)

    id: int
    stock_quantity: int
    created_at: datetime
    updated_at: datetime


class StockRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    product_id: int
    sku: str
    stock_quantity: int


class StockAdjust(BaseModel):
    """Positive delta restocks, negative delta removes stock (e.g. damage, loss)."""

    delta: int

    @field_validator("delta")
    @classmethod
    def delta_must_not_be_zero(cls, v: int) -> int:
        if v == 0:
            raise ValueError("delta must not be zero")
        return v
