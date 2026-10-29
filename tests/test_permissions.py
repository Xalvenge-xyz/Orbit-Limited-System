import pytest

def test_unapproved_cannot_access(client, app):
    with app.app_context():
        from backend.extensions import db
        from backend.models.user import User, Role
        r = Role.query.filter_by(name="cashier").first()
        u = User.query.filter_by(email="unapproved@orbit.local").first()
        if not u:
            u = User(full_name="UA", email="unapproved@orbit.local", role_id=r.id, status="pending")
            u.set_password("password123")
            db.session.add(u)
            db.session.commit()
    r = client.post("/auth/login", data={"email": "unapproved@orbit.local", "password": "password123"}, follow_redirects=False)
    # should not reach dashboard
    assert b"pending approval" in r.data or r.status_code == 200

def test_cashier_cannot_access_owner_finance(client, app):
    with app.app_context():
        from backend.extensions import db
        from backend.models.user import User, Role
        r = Role.query.filter_by(name="cashier").first()
        u = User.query.filter_by(email="cashier2@orbit.local").first()
        if not u:
            u = User(full_name="C2", email="cashier2@orbit.local", role_id=r.id, status="approved")
            u.set_password("password123")
            db.session.add(u)
            db.session.commit()
    client.post("/auth/login", data={"email": "cashier2@orbit.local", "password": "password123"}, follow_redirects=False)
    r = client.get("/finance/")
    assert r.status_code in (302, 403)
    r = client.get("/employees/")
    assert r.status_code in (302, 403)

def test_unauthorized_role_change_rejected(client, owner, app):
    # cashier cannot change roles -> 403
    with app.app_context():
        from backend.extensions import db
        from backend.models.user import User, Role
        r = Role.query.filter_by(name="cashier").first()
        u = User.query.filter_by(email="cashier3@orbit.local").first()
        if not u:
            u = User(full_name="C3", email="cashier3@orbit.local", role_id=r.id, status="approved")
            u.set_password("password123")
            db.session.add(u)
            db.session.commit()
    client.post("/auth/login", data={"email": "cashier3@orbit.local", "password": "password123"}, follow_redirects=False)
    r = client.post("/employees/api/1/role", json={"role_id": 1})
    assert r.status_code in (302, 403)
