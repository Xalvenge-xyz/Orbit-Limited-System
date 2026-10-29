from app import app
from backend.extensions import db
from backend.models.user import User, Role, ROLE_PERMISSIONS

with app.app_context():
    for name, perms in ROLE_PERMISSIONS.items():
        if not Role.query.filter_by(name=name).first():
            db.session.add(Role(name=name, description=name.title(), permissions=",".join(perms)))
    db.session.commit()
    r = Role.query.filter_by(name="owner").first()
    if not User.query.filter_by(email="owner@orbit.local").first():
        u = User(full_name="Owner", email="orbitlimited29@gmail.com", mobile="0917", role_id=r.id, status="approved")
        u.set_password("password123")
        db.session.add(u)
        db.session.commit()
        print("owner created", u.id)
    else:
        print("owner exists")
