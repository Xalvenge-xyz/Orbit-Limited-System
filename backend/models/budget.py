from datetime import datetime, timezone
from backend.extensions import db


class Budget(db.Model):
    __tablename__ = "budgets"
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(120), nullable=False)
    category = db.Column(db.String(80))
    amount = db.Column(db.Numeric(12, 2), nullable=False, default=0)
    period_start = db.Column(db.Date)
    period_end = db.Column(db.Date)
    safe_spend_percent = db.Column(db.Integer, default=30)
    notes = db.Column(db.Text)
    user_id = db.Column(db.Integer, db.ForeignKey("users.id"), nullable=True)
    created_at = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc))
    updated_at = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc), onupdate=lambda: datetime.now(timezone.utc))

    user = db.relationship("User", lazy="joined")
