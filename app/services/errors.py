class ProductNotFoundError(Exception):
    def __init__(self, product_ids: list[int]):
        self.product_ids = sorted(product_ids)
        super().__init__(f"Product(s) not found: {self.product_ids}")


class InsufficientStockError(Exception):
    def __init__(self, shortages: list[tuple[int, int, int]]):
        """shortages: list of (product_id, requested, available)."""
        self.shortages = shortages
        details = "; ".join(
            f"product {pid} (requested {req}, available {avail})"
            for pid, req, avail in shortages
        )
        super().__init__(f"Insufficient stock for {details}")
