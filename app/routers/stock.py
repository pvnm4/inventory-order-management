from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.db.session import get_db
from app.models import Product
from app.schemas import StockAdjust, StockRead
from app.services import stock_service
from app.services.errors import InsufficientStockError, ProductNotFoundError

router = APIRouter(prefix="/products/{product_id}/stock", tags=["stock"])
DbSession = Annotated[Session, Depends(get_db)]


def _to_read(product: Product) -> StockRead:
    return StockRead(
        product_id=product.id, sku=product.sku, stock_quantity=product.stock_quantity
    )


@router.get("", response_model=StockRead)
def get_stock(product_id: int, db: DbSession):
    product = db.get(Product, product_id)
    if product is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Product not found")
    return _to_read(product)


@router.patch("", response_model=StockRead)
def adjust_stock(product_id: int, payload: StockAdjust, db: DbSession):
    try:
        product = stock_service.adjust_stock(db, product_id, payload.delta)
    except ProductNotFoundError:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Product not found")
    except InsufficientStockError as exc:
        raise HTTPException(status.HTTP_409_CONFLICT, str(exc))
    return _to_read(product)
