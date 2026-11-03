from datetime import date, datetime, time, timedelta, timezone
from decimal import Decimal
from pathlib import Path

from sqlalchemy import Integer, bindparam, text
from sqlalchemy.orm import Session

from app.schemas import LowStockItem, SalesReport, SalesRow

SQL_DIR = Path(__file__).resolve().parents[2] / "sql"


def _load(name: str) -> str:
    return (SQL_DIR / name).read_text()


def low_stock(db: Session, threshold: int | None = None) -> list[LowStockItem]:
    stmt = text(_load("low_stock.sql")).bindparams(bindparam("threshold", type_=Integer))
    rows = db.execute(stmt, {"threshold": threshold}).mappings().all()
    return [LowStockItem(**row) for row in rows]


def sales(db: Session, start_date: date, end_date: date) -> SalesReport:
    """Sales per product for start_date..end_date inclusive (UTC days)."""
    start_ts = datetime.combine(start_date, time.min, tzinfo=timezone.utc)
    end_ts = datetime.combine(end_date + timedelta(days=1), time.min, tzinfo=timezone.utc)

    rows = db.execute(
        text(_load("sales_report.sql")), {"start_ts": start_ts, "end_ts": end_ts}
    ).mappings().all()

    items = [SalesRow(**row) for row in rows]
    return SalesReport(
        start_date=start_date,
        end_date=end_date,
        total_units=sum(i.units_sold for i in items),
        total_revenue=sum((i.revenue for i in items), Decimal("0.00")),
        items=items,
    )
