from datetime import datetime, timezone
from decimal import Decimal
from backend.extensions import db


class Debt(db.Model):
    __tablename__ = "debts"
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(150), nullable=False)
    debt_type = db.Column(db.String(20), nullable=False)  # receivable/payable (customer/supplier)
    amount = db.Column(db.Numeric(12, 2), nullable=False)
    paid_amount = db.Column(db.Numeric(12, 2), nullable=False, default=0)
    balance = db.Column(db.Numeric(12, 2), nullable=False, default=0)
    status = db.Column(db.String(20), default="unpaid", nullable=False)  # unpaid/partial/paid/overdue
    debt_date = db.Column(db.Date, nullable=False, index=True)
    due_date = db.Column(db.Date, nullable=True)
    notes = db.Column(db.Text)
    reference_type = db.Column(db.String(40))  # sale/purchase
    reference_id = db.Column(db.Integer)
    supplier_id = db.Column(db.Integer, db.ForeignKey("suppliers.id"), nullable=True)
    user_id = db.Column(db.Integer, db.ForeignKey("users.id"), nullable=True)
    created_at = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc))

    supplier = db.relationship("Supplier", lazy="joined")
    user = db.relationship("User", lazy="joined")
    payments = db.relationship("DebtPayment", backref="debt", lazy="selectin", cascade="all, delete-orphan")

    def recompute(self):
        total_paid = sum((p.amount for p in self.payments), Decimal(0))
        self.paid_amount = total_paid
        self.balance = self.amount - total_paid
        if self.balance <= 0:
            self.status = "paid"
            self.balance = Decimal(0) if self.balance < 0 else self.balance
        elif total_paid > 0:
            self.status = "partial"
        else:
            self.status = "unpaid"


class DebtPayment(db.Model):
    __tablename__ = "debt_payments"
    id = db.Column(db.Integer, primary_key=True)
    debt_id = db.Column(db.Integer, db.ForeignKey("debts.id"), nullable=False, index=True)
    amount = db.Column(db.Numeric(12, 2), nullable=False)
    payment_date = db.Column(db.Date, nullable=False, index=True)
    method = db.Column(db.String(30), default="cash")
    notes = db.Column(db.String(255))
    user_id = db.Column(db.Integer, db.ForeignKey("users.id"), nullable=True)
    created_at = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc))

    user = db.relationship("User", lazy="joined")
