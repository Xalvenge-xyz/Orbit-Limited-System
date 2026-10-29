import pytest
from app import create_app
from backend.extensions import db
from backend.models.user import User, Role, ROLE_PERMISSIONS


@pytest.fixture
def app():
    app = create_app()
    app.config["TESTING"] = True
    app.config["WTF_CSRF_ENABLED"] = False
    with app.app_context():
        for name, perms in ROLE_PERMISSIONS.items():
            if not Role.query.filter_by(name=name).first():
                db.session.add(Role(name=name, description=name.title(), permissions=",".join(perms)))
        db.session.commit()
    yield app


@pytest.fixture
def client(app):
    return app.test_client()


@pytest.fixture(autouse=True)
def reset_rate_limiter():
    from backend.utils import decorators
    decorators._buckets.clear()
    yield
    decorators._buckets.clear()

@pytest.fixture
def db_session(app):
    with app.app_context():
        yield db.session
        db.session.rollback()


@pytest.fixture
def owner(app, db_session):
    with app.app_context():
        r = Role.query.filter_by(name="owner").first()
        u = User.query.filter_by(email="testowner@orbit.local").first()
        if not u:
            u = User(full_name="Test Owner", email="testowner@orbit.local", role_id=r.id, status="approved")
            u.set_password("password123")
            db.session.add(u)
            db.session.commit()
        yield u
        # cleanup sales/products? leave
