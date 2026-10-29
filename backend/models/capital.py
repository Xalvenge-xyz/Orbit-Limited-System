from datetime import datetime, timezone
from backend.extensions import db


class CapitalTransaction(db.Model):
    __tablename__ = "capital_transactions"
    id = db.Column(db.Integer, primary_key=True)
    transaction_type = db.Column(db.String(30), nullable=False)  # contribution/withdrawal/adjustment
    amount = db.Column(db.Numeric(12, 2), nullable=False)
    description = db.Column(db.String(255))
    transaction_date = db.Column(db.Date, nullable=False, index=True)
    user_id = db.Column(db.Integer, db.ForeignKey("users.id"), nullable=True)
    created_at = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc))

    user = db.relationship("User", lazy="joined")
