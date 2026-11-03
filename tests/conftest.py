import os

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker

import app.models  # noqa: F401
from app.core.config import normalize_db_url
from app.db.base import Base
from app.db.session import get_db
from app.main import app

TEST_DATABASE_URL = normalize_db_url(
    os.getenv(
        "TEST_DATABASE_URL",
        "postgresql://postgres:postgres@localhost:5432/inventory_test",
    )
)


@pytest.fixture(scope="session")
def engine():
    # Large pool so the concurrency tests can run many requests at once.
    eng = create_engine(TEST_DATABASE_URL, pool_size=30, max_overflow=0)
    Base.metadata.drop_all(eng)
    Base.metadata.create_all(eng)
    yield eng
    Base.metadata.drop_all(eng)
    eng.dispose()


@pytest.fixture(autouse=True)
def clean_db(engine):
    with engine.begin() as conn:
        conn.execute(text("TRUNCATE order_items, orders, products RESTART IDENTITY CASCADE"))


@pytest.fixture
def session_factory(engine):
    return sessionmaker(bind=engine, autoflush=False, expire_on_commit=False)


@pytest.fixture(autouse=True)
def override_db(session_factory):
    def _get_db():
        db = session_factory()
        try:
            yield db
        finally:
            db.close()

    app.dependency_overrides[get_db] = _get_db
    yield
    app.dependency_overrides.clear()


@pytest.fixture
def client():
    return TestClient(app)


@pytest.fixture
def make_product(client):
    counter = {"n": 0}

    def _make(**overrides):
        counter["n"] += 1
        payload = {
            "sku": f"SKU-{counter['n']:03d}",
            "name": f"Product {counter['n']}",
            "price": "10.00",
            "stock_quantity": 10,
        }
        payload.update(overrides)
        resp = client.post("/products", json=payload)
        assert resp.status_code == 201, resp.text
        return resp.json()

    return _make


def get_stock(client, product_id: int) -> int:
    return client.get(f"/products/{product_id}/stock").json()["stock_quantity"]
