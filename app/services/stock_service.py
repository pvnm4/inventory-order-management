from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models import Product
from app.services.errors import InsufficientStockError, ProductNotFoundError


def adjust_stock(db: Session, product_id: int, delta: int) -> Product:
    """Apply a stock delta under a row lock; never lets stock go negative."""
    try:
        product = db.execute(
            select(Product).where(Product.id == product_id).with_for_update()
        ).scalar_one_or_none()
        if product is None:
            raise ProductNotFoundError([product_id])

        new_quantity = product.stock_quantity + delta
        if new_quantity < 0:
            raise InsufficientStockError([(product_id, -delta, product.stock_quantity)])

        product.stock_quantity = new_quantity
        db.commit()
    except Exception:
        db.rollback()
        raise
    return product
