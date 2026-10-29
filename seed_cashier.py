from app import app
from backend.extensions import db
from backend.models.user import User, Role

with app.app_context():
    r = Role.query.filter_by(name="cashier").first()
    if not User.query.filter_by(email="cashier@orbit.local").first():
        u = User(full_name="Cashier", email="cashier@orbit.local", mobile="0918", role_id=r.id, status="approved")
        u.set_password("password123")
        db.session.add(u)
        db.session.commit()
        print("cashier created", u.id)
    else:
        print("exists")
