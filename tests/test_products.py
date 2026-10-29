import pytest
import uuid

def test_recommended_min_price():
    from backend.services.pricing_service import PricingService
    from decimal import Decimal
    rec = PricingService.recommended_min_price(100, 0.20)
    assert rec == Decimal("125.00")

def test_recommended_invalid_margin():
    from backend.services.pricing_service import PricingService
    assert PricingService.recommended_min_price(100, 1.0) is None
    assert PricingService.recommended_min_price(100, -0.1) is None

def test_product_create_and_duplicate_sku(owner, app):
    sku = "TP-" + uuid.uuid4().hex[:8]
    with app.test_client() as c:
        _r = c.post("/auth/login", data={"email": "testowner@orbit.local", "password": "password123"}, follow_redirects=False)
        print("PROD LOGIN", _r.status_code, _r.headers.get("Location"))
        r = c.post("/products/api/create", json={"name": "TestProd", "sku": sku, "cost": 10, "price": 20, "min_price": 15, "stock": 5})
        print("PROD CREATE", r.status_code)
        assert r.status_code == 200
        r2 = c.post("/products/api/create", json={"name": "TestProd2", "sku": sku, "cost": 10, "price": 20, "min_price": 15, "stock": 5})
        assert r2.status_code == 400

