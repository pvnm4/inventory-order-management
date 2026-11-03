from datetime import date
from decimal import Decimal

from pydantic import BaseModel


class LowStockItem(BaseModel):
    product_id: int
    sku: str
    name: str
    stock_quantity: int
    threshold: int


class SalesRow(BaseModel):
    product_id: int
    sku: str
    name: str
    units_sold: int
    revenue: Decimal


class SalesReport(BaseModel):
    start_date: date
    end_date: date
    total_units: int
    total_revenue: Decimal
    items: list[SalesRow]
