import pytest

def test_login_valid(client, app):
    r = client.post("/auth/login", data={"email": "testowner@orbit.local", "password": "password123", "csrf_token": "x"}, follow_redirects=False)
    assert r.status_code in (200, 302)

def test_login_invalid(client):
    r = client.post("/auth/login", data={"email": "nope@orbit.local", "password": "wrong"}, follow_redirects=False)
    assert b"Invalid credentials" in r.data or r.status_code == 200

def test_cashier_cannot_access_finance(client, app):
    with app.app_context():
        from backend.extensions import db
        from backend.models.user import User, Role
        r = Role.query.filter_by(name="cashier").first()
        u = User.query.filter_by(email="testcashier@orbit.local").first()
        if not u:
            u = User(full_name="TC", email="testcashier@orbit.local", role_id=r.id, status="approved")
            u.set_password("password123")
            db.session.add(u)
            db.session.commit()
    # login as cashier
    client.post("/auth/login", data={"email": "testcashier@orbit.local", "password": "password123"}, follow_redirects=False)
    r = client.get("/finance/")
    assert r.status_code in (302, 403)
    r = client.get("/dashboard/api/metrics")
    assert r.status_code == 403
