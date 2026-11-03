from collections import defaultdict
from decimal import Decimal

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models import Order, OrderItem, Product
from app.schemas import OrderCreate
from app.services.errors import InsufficientStockError, ProductNotFoundError


def place_order(db: Session, payload: OrderCreate) -> Order:
    """Place an order atomically.

    Everything happens in ONE transaction:
      1. lock the affected product rows (SELECT ... FOR UPDATE),
      2. verify every line has enough stock,
      3. deduct stock and create the order + items,
      4. commit - or roll everything back if anything fails.

    Rows are locked in ascending id order, so two orders touching the same
    products in different orders cannot deadlock, and two orders competing for
    the last units are serialised: the second sees the updated stock and fails.
    """
    # Merge duplicate lines for the same product.
    requested: dict[int, int] = defaultdict(int)
    for item in payload.items:
        requested[item.product_id] += item.quantity

    try:
        products = (
            db.execute(
                select(Product)
                .where(Product.id.in_(list(requested)))
                .order_by(Product.id)
                .with_for_update()
            )
            .scalars()
            .all()
        )
        by_id = {p.id: p for p in products}

        missing = [pid for pid in requested if pid not in by_id]
        if missing:
            raise ProductNotFoundError(missing)

        shortages = [
            (pid, qty, by_id[pid].stock_quantity)
            for pid, qty in requested.items()
            if by_id[pid].stock_quantity < qty
        ]
        if shortages:
            raise InsufficientStockError(shortages)

        order = Order(status="confirmed", total_amount=Decimal("0.00"))
        total = Decimal("0.00")
        for pid, qty in requested.items():
            product = by_id[pid]
            product.stock_quantity -= qty
            order.items.append(
                OrderItem(product_id=pid, quantity=qty, unit_price=product.price)
            )
            total += product.price * qty
        order.total_amount = total

        db.add(order)
        db.commit()
    except Exception:
        db.rollback()
        raise

    return get_order(db, order.id)  # reload server-generated fields (created_at)


def get_order(db: Session, order_id: int) -> Order | None:
    return db.get(Order, order_id, populate_existing=True)


def list_orders(db: Session, skip: int = 0, limit: int = 50) -> list[Order]:
    stmt = select(Order).order_by(Order.id.desc()).offset(skip).limit(limit)
    return list(db.execute(stmt).scalars().all())
