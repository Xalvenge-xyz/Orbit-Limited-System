from backend.extensions import db
from backend.models.product import Product
from backend.models.debt import Debt


class NotificationService:
    @staticmethod
    def low_stock_products(threshold=None):
        from flask import current_app
        thr = threshold or current_app.config.get("LOW_STOCK_THRESHOLD", 3)
        out = []
        for p in Product.query.filter_by(status="active").all():
            if p.stock <= (p.reorder_level or thr) or p.stock <= thr:
                out.append(p)
        return out

    @staticmethod
    def overdue_debts():
        from datetime import date
        out = []
        for d in Debt.query.filter(Debt.status != "paid").all():
            if d.due_date and d.due_date < date.today():
                out.append(d)
        return out

    @staticmethod
    def pending_accounts():
        from backend.models.user import User
        return User.query.filter_by(status="pending").all()
