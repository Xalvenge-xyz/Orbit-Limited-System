from datetime import datetime, timezone, date, timedelta
from decimal import Decimal
from backend.extensions import db
from backend.models.sale import Sale
from backend.models.expense import Expense
from backend.models.product import Product
# removed bad import line



class ReportingService:
    @staticmethod
    def parse_range(period, start=None, end=None):
        today = date.today()
        if period == "daily":
            s = datetime.combine(today, datetime.min.time())
            e = datetime.combine(today, datetime.max.time())
        elif period == "weekly":
            s = datetime.combine(today - timedelta(days=6), datetime.min.time())
            e = datetime.combine(today, datetime.max.time())
        elif period == "monthly":
            first = today.replace(day=1)
            s = datetime.combine(first, datetime.min.time())
            e = datetime.combine(today, datetime.max.time())
        else:
            try:
                s = datetime.fromisoformat(start) if start else datetime.combine(today - timedelta(days=30), datetime.min.time())
            except Exception:
                s = datetime.combine(today - timedelta(days=30), datetime.min.time())
            try:
                e = datetime.fromisoformat(end) if end else datetime.combine(today, datetime.max.time())
            except Exception:
                e = datetime.combine(today, datetime.max.time())
            if isinstance(s, date) and not isinstance(s, datetime):
                s = datetime.combine(s, datetime.min.time())
            if isinstance(e, date) and not isinstance(e, datetime):
                e = datetime.combine(e, datetime.max.time())
        return s, e

    @staticmethod
    def sales_report(s, e):
        q = Sale.query.filter(Sale.created_at >= s, Sale.created_at <= e, Sale.status == "completed")
        return q.order_by(Sale.created_at.desc()).all()

    @staticmethod
    def stock_movements(s, e):
        from backend.models.inventory import StockMovement
        q = StockMovement.query.filter(StockMovement.created_at >= s, StockMovement.created_at <= e)
        return q.order_by(StockMovement.created_at.desc()).all()
