from tests.conftest import get_stock


def test_create_and_get_product(client):
    resp = client.post(
        "/products",
        json={"sku": "ABC-1", "name": "Widget", "price": "9.99", "stock_quantity": 5},
    )
    assert resp.status_code == 201
    body = resp.json()
    assert body["sku"] == "ABC-1"
    assert body["stock_quantity"] == 5
    assert body["low_stock_threshold"] == 10

    fetched = client.get(f"/products/{body['id']}")
    assert fetched.status_code == 200
    assert fetched.json()["name"] == "Widget"


def test_duplicate_sku_returns_409(client, make_product):
    make_product(sku="DUP")
    resp = client.post("/products", json={"sku": "DUP", "name": "x", "price": "1.00"})
    assert resp.status_code == 409


def test_get_missing_product_returns_404(client):
    assert client.get("/products/999").status_code == 404


def test_validation_rejects_bad_input(client):
    assert client.post("/products", json={"sku": "A", "name": "x", "price": "-1"}).status_code == 422
    assert client.post("/products", json={"sku": "", "name": "x", "price": "1"}).status_code == 422
    assert (
        client.post(
            "/products", json={"sku": "A", "name": "x", "price": "1", "stock_quantity": -3}
        ).status_code
        == 422
    )


def test_list_products_with_pagination(client, make_product):
    for _ in range(5):
        make_product()
    page1 = client.get("/products", params={"limit": 2}).json()
    page2 = client.get("/products", params={"skip": 2, "limit": 2}).json()
    assert [p["id"] for p in page1] == [1, 2]
    assert [p["id"] for p in page2] == [3, 4]


def test_update_product_does_not_touch_stock(client, make_product):
    product = make_product(stock_quantity=7)
    resp = client.put(
        f"/products/{product['id']}",
        json={"name": "Renamed", "price": "12.50", "stock_quantity": 999},
    )
    assert resp.status_code == 200
    assert resp.json()["name"] == "Renamed"
    assert resp.json()["price"] == "12.50"
    assert get_stock(client, product["id"]) == 7  # stock changes only via /stock


def test_delete_product(client, make_product):
    product = make_product()
    assert client.delete(f"/products/{product['id']}").status_code == 204
    assert client.get(f"/products/{product['id']}").status_code == 404


def test_cannot_delete_product_with_orders(client, make_product):
    product = make_product()
    client.post("/orders", json={"items": [{"product_id": product["id"], "quantity": 1}]})
    assert client.delete(f"/products/{product['id']}").status_code == 409
    assert client.get(f"/products/{product['id']}").status_code == 200


def test_stock_adjustment(client, make_product):
    product = make_product(stock_quantity=5)
    pid = product["id"]

    assert client.patch(f"/products/{pid}/stock", json={"delta": 10}).json()["stock_quantity"] == 15
    assert client.patch(f"/products/{pid}/stock", json={"delta": -4}).json()["stock_quantity"] == 11


def test_stock_cannot_go_negative(client, make_product):
    product = make_product(stock_quantity=3)
    pid = product["id"]
    assert client.patch(f"/products/{pid}/stock", json={"delta": -4}).status_code == 409
    assert get_stock(client, pid) == 3


def test_stock_adjustment_validation_and_404(client, make_product):
    product = make_product()
    assert client.patch(f"/products/{product['id']}/stock", json={"delta": 0}).status_code == 422
    assert client.patch("/products/999/stock", json={"delta": 1}).status_code == 404
    assert client.get("/products/999/stock").status_code == 404
