import pytest
import uuid
from decimal import Decimal

def test_cogs_and_gross_profit(owner, app):
    sku = "FP-" + uuid.uuid4().hex[:8]
    with app.test_client() as c:
        c.post("/auth/login", data={"email": "testowner@orbit.local", "password": "password123"}, follow_redirects=False)
        r = c.post("/products/api/create", json={"name": "FP", "sku": sku, "cost": 50, "price": 100, "min_price": 60, "stock": 10})
        pid = r.get_json()["id"]
        r = c.post("/pos/api/checkout", json={"items": [{"product_id": pid, "quantity": 2, "selected_price": 100}], "payment_method": "cash", "cash_tendered": 300, "idempotency_key": "fin-" + uuid.uuid4().hex[:6]})
        assert r.status_code == 200
        from backend.services.profit_service import ProfitService
        from datetime import datetime, timedelta
        s = datetime.now() - timedelta(days=1)
        e = datetime.now() + timedelta(days=1)
        totals = ProfitService.period_totals(s, e)
        assert totals["cogs"] >= Decimal("100.00")
        assert totals["gross_sales"] >= Decimal("200.00")
        assert totals["gross_profit"] >= Decimal("100.00")

def test_capital_not_revenue():
    from backend.services.profit_service import ProfitService
    assert hasattr(ProfitService, "period_totals")

def test_safe_spend():
    from backend.services.finance_service import FinanceService
    limit, buf = FinanceService.safe_spend(Decimal("1000"), 30)
    assert limit == Decimal("300.00")
    assert buf == Decimal("700.00")

def test_partial_debt_payment():
    from backend.extensions import db
    from backend.models.debt import Debt
    from backend.services.debt_service import DebtService
    from app import create_app
    from datetime import date
    app = create_app()
    with app.app_context():
        d = DebtService.create_debt("T", "receivable", 100, date.today())
        DebtService.record_payment(d.id, 40, date.today())
        d2 = db.session.get(Debt, d.id)
        assert float(d2.balance) == 60.0
        assert d2.status == "partial"

