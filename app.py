import os
from flask import Flask, render_template, redirect, request
from config import Config
from backend.extensions import db, migrate, login_manager, csrf

# Import models so migrations see them
import backend.models  # noqa


def create_app(config_class=Config):
    app = Flask(__name__)
    app.config.from_object(config_class)

    db.init_app(app)
    migrate.init_app(app, db)
    login_manager.init_app(app)
    csrf.init_app(app)
    from backend.extensions import mail
    mail.init_app(app)

    from backend.models.user import User

    @login_manager.user_loader
    def load_user(user_id):
        try:
            return db.session.get(User, int(user_id))
        except Exception:
            return None

    # Register blueprints
    from backend.routes.auth import auth_bp
    from backend.routes.dashboard import dashboard_bp
    from backend.routes.products import products_bp
    from backend.routes.inventory import inventory_bp
    from backend.routes.pos import pos_bp
    from backend.routes.sales import sales_bp
    from backend.routes.expenses import expenses_bp
    from backend.routes.finance import finance_bp
    from backend.routes.debts import debts_bp
    from backend.routes.purchases import purchases_bp
    from backend.routes.reports import reports_bp
    from backend.routes.employees import employees_bp
    from backend.routes.settings import settings_bp

    app.register_blueprint(auth_bp)
    app.register_blueprint(dashboard_bp)
    app.register_blueprint(products_bp)
    app.register_blueprint(inventory_bp)
    app.register_blueprint(pos_bp)
    app.register_blueprint(sales_bp)
    app.register_blueprint(expenses_bp)
    app.register_blueprint(finance_bp)
    app.register_blueprint(debts_bp)
    app.register_blueprint(purchases_bp)
    app.register_blueprint(reports_bp)
    app.register_blueprint(employees_bp)
    app.register_blueprint(settings_bp)

    # Error handlers
    @app.errorhandler(403)
    def forbidden(e):
        return render_template("errors/403.html"), 403

    @app.errorhandler(404)
    def not_found(e):
        return render_template("errors/404.html"), 404

    @app.errorhandler(500)
    def server_error(e):
        return render_template("errors/500.html"), 500

    return app


from datetime import timezone, timedelta

PHT = timezone(timedelta(hours=8))

def to_pht(dt):
    if dt is None:
        return ""
    if dt.tzinfo is None:
        dt = dt.replace(tzinfo=timezone.utc)
    return dt.astimezone(PHT).strftime("%Y-%m-%d %I:%M %p")

# register after app creation
app = create_app()
app.jinja_env.filters['ph'] = to_pht

@app.after_request
def _cache_static(response):
    if request.path.startswith("/static/"):
        response.headers["Cache-Control"] = "public, max-age=31536000, immutable"
    return response

@app.route("/")
def landing():
    from flask_login import current_user
    if current_user.is_authenticated:
        return redirect("/dashboard")
    return render_template("landing.html")

if __name__ == "__main__":
    app.run(debug=True, host="0.0.0.0", port=5000)
