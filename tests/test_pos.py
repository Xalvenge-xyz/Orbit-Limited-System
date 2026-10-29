import pytest
import uuid

def test_checkout_valid_and_idempotency(app):
    sku = "PP-" + uuid.uuid4().hex[:8]
    email = "testowner@orbit.local"
    with app.test_client() as c:
        c.post("/auth/login", data={"email": email, "password": "password123"}, follow_redirects=False)
        r = c.post("/products/api/create", json={"name": "POSProd", "sku": sku, "cost": 4, "price": 10, "min_price": 6, "stock": 10})
        pid = r.get_json()["id"]
        key = "pos-idem-" + uuid.uuid4().hex[:8]
        r = c.post("/pos/api/checkout", json={"items": [{"product_id": pid, "quantity": 2, "selected_price": 10}], "payment_method": "cash", "cash_tendered": 50, "idempotency_key": key})
        assert r.status_code == 200
        sale_number = r.get_json()["sale_number"]
        r2 = c.post("/pos/api/checkout", json={"items": [{"product_id": pid, "quantity": 2, "selected_price": 10}], "payment_method": "cash", "cash_tendered": 50, "idempotency_key": key})
        assert r2.status_code == 200
        assert r2.get_json()["sale_number"] == sale_number
        r = c.get(f"/products/api/{pid}")
        assert r.get_json()["stock"] == 8

def test_empty_cart_rejected(app):
    import uuid
    email = f"owner-{uuid.uuid4().hex[:8]}@orbit.local"
    with app.app_context():
        from backend.extensions import db
        from backend.models.user import User, Role
        r = Role.query.filter_by(name="owner").first()
        u = User(full_name="O", email=email, role_id=r.id, status="approved")
        u.set_password("password123")
        db.session.add(u)
        db.session.commit()
    with app.test_client() as c:
        c.post("/auth/login", data={"email": email, "password": "password123"}, follow_redirects=False)
        r = c.post("/pos/api/checkout", json={"items": [], "payment_method": "cash", "cash_tendered": 0, "idempotency_key": "empty-" + uuid.uuid4().hex[:6]})
        assert r.status_code == 400

def test_insufficient_cash_rejected(app):
    sku = "P3-" + uuid.uuid4().hex[:8]
    email = "testowner@orbit.local"
    with app.test_client() as c:
        c.post("/auth/login", data={"email": email, "password": "password123"}, follow_redirects=False)
        r = c.post("/products/api/create", json={"name": "P3", "sku": sku, "cost": 4, "price": 10, "min_price": 6, "stock": 10})
        pid = r.get_json()["id"]
        r = c.post("/pos/api/checkout", json={"items": [{"product_id": pid, "quantity": 1, "selected_price": 10}], "payment_method": "cash", "cash_tendered": 5, "idempotency_key": "cash-" + uuid.uuid4().hex[:6]})
        assert r.status_code == 400
        assert "Insufficient cash" in r.get_json()["error"]









