from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session

from app.db.session import get_db
from app.schemas import OrderCreate, OrderRead
from app.services import order_service
from app.services.errors import InsufficientStockError, ProductNotFoundError

router = APIRouter(prefix="/orders", tags=["orders"])
DbSession = Annotated[Session, Depends(get_db)]


@router.post("", response_model=OrderRead, status_code=status.HTTP_201_CREATED)
def place_order(payload: OrderCreate, db: DbSession):
    try:
        return order_service.place_order(db, payload)
    except ProductNotFoundError as exc:
        raise HTTPException(status.HTTP_404_NOT_FOUND, str(exc))
    except InsufficientStockError as exc:
        raise HTTPException(status.HTTP_409_CONFLICT, str(exc))


@router.get("", response_model=list[OrderRead])
def list_orders(
    db: DbSession,
    skip: int = Query(0, ge=0),
    limit: int = Query(50, ge=1, le=200),
):
    return order_service.list_orders(db, skip, limit)


@router.get("/{order_id}", response_model=OrderRead)
def get_order(order_id: int, db: DbSession):
    order = order_service.get_order(db, order_id)
    if order is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Order not found")
    return order
