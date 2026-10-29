import pytest
import uuid

def test_stock_not_negative(owner, app):
    sku = "LS-" + uuid.uuid4().hex[:8]
    with app.test_client() as c:
        c.post("/auth/login", data={"email": "testowner@orbit.local", "password": "password123"}, follow_redirects=False)
        r = c.post("/products/api/create", json={"name": "LowStock", "sku": sku, "cost": 5, "price": 10, "min_price": 7, "stock": 2})
        pid = r.get_json()["id"]
        r = c.post("/pos/api/checkout", json={"items": [{"product_id": pid, "quantity": 5, "selected_price": 10}], "payment_method": "cash", "cash_tendered": 100, "idempotency_key": "inv-1-" + uuid.uuid4().hex[:6]})
        assert r.status_code == 400
        r = c.get(f"/products/api/{pid}")
        assert r.get_json()["stock"] == 2

def test_failed_checkout_no_partial(owner, app):
    sku = "P2-" + uuid.uuid4().hex[:8]
    with app.test_client() as c:
        c.post("/auth/login", data={"email": "testowner@orbit.local", "password": "password123"}, follow_redirects=False)
        r = c.post("/products/api/create", json={"name": "P2", "sku": sku, "cost": 5, "price": 10, "min_price": 7, "stock": 5})
        pid = r.get_json()["id"]
        r = c.post("/pos/api/checkout", json={"items": [{"product_id": pid, "quantity": 1, "selected_price": 10}], "payment_method": "cash", "cash_tendered": 1, "idempotency_key": "inv-2-" + uuid.uuid4().hex[:6]})
        assert r.status_code == 400
        r = c.get(f"/products/api/{pid}")
        assert r.get_json()["stock"] == 5

