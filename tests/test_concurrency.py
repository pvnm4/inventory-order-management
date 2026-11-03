"""Concurrency tests: these only mean something against a real PostgreSQL database."""
from concurrent.futures import ThreadPoolExecutor

from fastapi.testclient import TestClient

from app.main import app
from tests.conftest import get_stock


def _place(items):
    # One client per thread; each request gets its own DB session/connection.
    with TestClient(app) as c:
        return c.post("/orders", json={"items": items}).status_code


def test_concurrent_orders_never_oversell(client, make_product):
    product = make_product(stock_quantity=5)
    pid = product["id"]

    with ThreadPoolExecutor(max_workers=20) as pool:
        futures = [pool.submit(_place, [{"product_id": pid, "quantity": 1}]) for _ in range(20)]
        statuses = [f.result() for f in futures]

    assert statuses.count(201) == 5
    assert statuses.count(409) == 15
    assert get_stock(client, pid) == 0
    assert len(client.get("/orders", params={"limit": 200}).json()) == 5


def test_concurrent_multi_unit_orders_never_exceed_stock(client, make_product):
    product = make_product(stock_quantity=10)
    pid = product["id"]

    with ThreadPoolExecutor(max_workers=12) as pool:
        futures = [pool.submit(_place, [{"product_id": pid, "quantity": 3}]) for _ in range(12)]
        statuses = [f.result() for f in futures]

    successes = statuses.count(201)
    assert successes == 3  # 3 x 3 = 9 <= 10, a 4th would need 12
    assert get_stock(client, pid) == 10 - successes * 3
    assert get_stock(client, pid) >= 0


def test_opposite_lock_order_orders_do_not_deadlock(client, make_product):
    a = make_product(stock_quantity=50)
    b = make_product(stock_quantity=50)
    forward = [{"product_id": a["id"], "quantity": 1}, {"product_id": b["id"], "quantity": 1}]
    backward = [{"product_id": b["id"], "quantity": 1}, {"product_id": a["id"], "quantity": 1}]

    with ThreadPoolExecutor(max_workers=20) as pool:
        futures = [pool.submit(_place, forward if i % 2 == 0 else backward) for i in range(20)]
        statuses = [f.result() for f in futures]

    assert statuses == [201] * 20  # no deadlock errors, no 500s
    assert get_stock(client, a["id"]) == 30
    assert get_stock(client, b["id"]) == 30
