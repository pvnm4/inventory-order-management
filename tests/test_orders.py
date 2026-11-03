import pytest
from sqlalchemy import func, select

from app.models import Order, OrderItem
from app.services import order_service
from tests.conftest import get_stock


def test_place_order_deducts_stock_and_totals(client, make_product):
    a = make_product(price="10.00", stock_quantity=10)
    b = make_product(price="2.50", stock_quantity=4)

    resp = client.post(
        "/orders",
        json={
            "items": [
                {"product_id": a["id"], "quantity": 3},
                {"product_id": b["id"], "quantity": 2},
            ]
        },
    )
    assert resp.status_code == 201
    body = resp.json()
    assert body["status"] == "confirmed"
    assert body["total_amount"] == "35.00"
    assert len(body["items"]) == 2
    assert {i["product_id"]: i["line_total"] for i in body["items"]} == {
        a["id"]: "30.00",
        b["id"]: "5.00",
    }
    assert get_stock(client, a["id"]) == 7
    assert get_stock(client, b["id"]) == 2


def test_duplicate_lines_are_merged(client, make_product):
    p = make_product(stock_quantity=5)
    resp = client.post(
        "/orders",
        json={"items": [{"product_id": p["id"], "quantity": 2}, {"product_id": p["id"], "quantity": 2}]},
    )
    assert resp.status_code == 201
    assert len(resp.json()["items"]) == 1
    assert resp.json()["items"][0]["quantity"] == 4
    assert get_stock(client, p["id"]) == 1


def test_insufficient_stock_returns_409_and_changes_nothing(client, make_product):
    p = make_product(stock_quantity=2)
    resp = client.post("/orders", json={"items": [{"product_id": p["id"], "quantity": 3}]})
    assert resp.status_code == 409
    assert "Insufficient stock" in resp.json()["detail"]
    assert get_stock(client, p["id"]) == 2
    assert client.get("/orders").json() == []


def test_one_bad_line_rolls_back_the_whole_order(client, make_product):
    ok = make_product(stock_quantity=10)
    short = make_product(stock_quantity=1)
    resp = client.post(
        "/orders",
        json={
            "items": [
                {"product_id": ok["id"], "quantity": 5},
                {"product_id": short["id"], "quantity": 2},
            ]
        },
    )
    assert resp.status_code == 409
    assert get_stock(client, ok["id"]) == 10  # untouched even though this line was fine
    assert get_stock(client, short["id"]) == 1
    assert client.get("/orders").json() == []


def test_unknown_product_returns_404(client, make_product):
    p = make_product()
    resp = client.post(
        "/orders",
        json={"items": [{"product_id": p["id"], "quantity": 1}, {"product_id": 999, "quantity": 1}]},
    )
    assert resp.status_code == 404
    assert get_stock(client, p["id"]) == 10


@pytest.mark.parametrize(
    "payload",
    [
        {"items": []},
        {"items": [{"product_id": 1, "quantity": 0}]},
        {"items": [{"product_id": 1, "quantity": -2}]},
        {},
    ],
)
def test_invalid_order_payloads_return_422(client, payload):
    assert client.post("/orders", json=payload).status_code == 422


def test_failure_mid_transaction_rolls_back_stock(client, make_product, monkeypatch, session_factory):
    """Stock has already been deducted in the session when this blows up;
    the rollback must undo it and leave no order rows behind."""
    p = make_product(stock_quantity=10)

    def boom(*args, **kwargs):
        raise RuntimeError("simulated failure after stock deduction")

    monkeypatch.setattr(order_service, "OrderItem", boom)

    from fastapi.testclient import TestClient

    from app.main import app

    resp = TestClient(app, raise_server_exceptions=False).post(
        "/orders", json={"items": [{"product_id": p["id"], "quantity": 4}]}
    )
    assert resp.status_code == 500

    monkeypatch.undo()
    assert get_stock(client, p["id"]) == 10
    with session_factory() as db:
        assert db.scalar(select(func.count()).select_from(Order)) == 0
        assert db.scalar(select(func.count()).select_from(OrderItem)) == 0


def test_get_and_list_orders(client, make_product):
    p = make_product(stock_quantity=10)
    ids = [
        client.post("/orders", json={"items": [{"product_id": p["id"], "quantity": 1}]}).json()["id"]
        for _ in range(3)
    ]
    assert client.get(f"/orders/{ids[0]}").status_code == 200
    assert client.get("/orders/999").status_code == 404

    listing = client.get("/orders").json()
    assert [o["id"] for o in listing] == sorted(ids, reverse=True)  # newest first
    assert len(client.get("/orders", params={"limit": 2}).json()) == 2


def test_unit_price_is_snapshotted(client, make_product):
    p = make_product(price="10.00", stock_quantity=5)
    order = client.post("/orders", json={"items": [{"product_id": p["id"], "quantity": 1}]}).json()
    client.put(f"/products/{p['id']}", json={"price": "99.00"})
    again = client.get(f"/orders/{order['id']}").json()
    assert again["items"][0]["unit_price"] == "10.00"
    assert again["total_amount"] == "10.00"
