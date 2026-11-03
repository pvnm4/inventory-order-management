from datetime import date, timedelta


def test_low_stock_uses_each_products_threshold(client, make_product):
    make_product(sku="LOW", stock_quantity=3, low_stock_threshold=5)
    make_product(sku="EDGE", stock_quantity=5, low_stock_threshold=5)  # at threshold counts
    make_product(sku="OK", stock_quantity=50, low_stock_threshold=5)

    rows = client.get("/reports/low-stock").json()
    assert [r["sku"] for r in rows] == ["LOW", "EDGE"]  # lowest stock first
    assert rows[0]["threshold"] == 5


def test_low_stock_threshold_override(client, make_product):
    make_product(sku="A", stock_quantity=3, low_stock_threshold=1)
    make_product(sku="B", stock_quantity=20, low_stock_threshold=1)

    assert client.get("/reports/low-stock").json() == []
    rows = client.get("/reports/low-stock", params={"threshold": 25}).json()
    assert [r["sku"] for r in rows] == ["A", "B"]
    assert client.get("/reports/low-stock", params={"threshold": -1}).status_code == 422


def test_sales_report_aggregates_per_product(client, make_product):
    a = make_product(sku="A", price="10.00", stock_quantity=20)
    b = make_product(sku="B", price="3.00", stock_quantity=20)
    c = make_product(sku="C", price="1.00", stock_quantity=20)  # never sold

    client.post("/orders", json={"items": [{"product_id": a["id"], "quantity": 2}, {"product_id": b["id"], "quantity": 5}]})
    client.post("/orders", json={"items": [{"product_id": a["id"], "quantity": 1}]})

    today = date.today()
    resp = client.get(
        "/reports/sales",
        params={"start_date": str(today - timedelta(days=1)), "end_date": str(today + timedelta(days=1))},
    )
    assert resp.status_code == 200
    report = resp.json()

    rows = {r["sku"]: r for r in report["items"]}
    assert set(rows) == {"A", "B"} and c["sku"] not in rows
    assert rows["A"]["units_sold"] == 3 and rows["A"]["revenue"] == "30.00"
    assert rows["B"]["units_sold"] == 5 and rows["B"]["revenue"] == "15.00"
    assert report["total_units"] == 8
    assert report["total_revenue"] == "45.00"
    assert [r["sku"] for r in report["items"]] == ["A", "B"]  # revenue desc


def test_sales_report_outside_range_is_empty(client, make_product):
    p = make_product(stock_quantity=5)
    client.post("/orders", json={"items": [{"product_id": p["id"], "quantity": 1}]})
    report = client.get(
        "/reports/sales", params={"start_date": "2020-01-01", "end_date": "2020-01-31"}
    ).json()
    assert report["items"] == []
    assert report["total_units"] == 0
    assert report["total_revenue"] == "0.00"


def test_sales_report_validates_dates(client):
    assert client.get("/reports/sales").status_code == 422
    resp = client.get("/reports/sales", params={"start_date": "2026-02-01", "end_date": "2026-01-01"})
    assert resp.status_code == 400
