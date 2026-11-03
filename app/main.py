from fastapi import FastAPI

from app.routers import orders, products, reports, stock

app = FastAPI(
    title="Inventory & Order Management API",
    description="Products, stock and orders with atomic, oversell-proof order placement.",
    version="1.0.0",
)

app.include_router(products.router)
app.include_router(stock.router)
app.include_router(orders.router)
app.include_router(reports.router)


@app.get("/health", tags=["health"])
def health():
    return {"status": "ok"}
