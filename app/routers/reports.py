from datetime import date
from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session

from app.db.session import get_db
from app.schemas import LowStockItem, SalesReport
from app.services import report_service

router = APIRouter(prefix="/reports", tags=["reports"])
DbSession = Annotated[Session, Depends(get_db)]


@router.get("/low-stock", response_model=list[LowStockItem])
def low_stock_report(
    db: DbSession,
    threshold: int | None = Query(
        None, ge=0, description="Override; defaults to each product's own threshold"
    ),
):
    return report_service.low_stock(db, threshold)


@router.get("/sales", response_model=SalesReport)
def sales_report(
    db: DbSession,
    start_date: date = Query(..., description="First day (inclusive, UTC)"),
    end_date: date = Query(..., description="Last day (inclusive, UTC)"),
):
    if start_date > end_date:
        raise HTTPException(status.HTTP_400_BAD_REQUEST, "start_date must be <= end_date")
    return report_service.sales(db, start_date, end_date)
