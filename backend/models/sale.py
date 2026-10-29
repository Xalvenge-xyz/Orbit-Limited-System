from datetime import datetime, timezone
from decimal import Decimal
from backend.extensions import db


class Sale(db.Model):
    __tablename__ = "sales"
    id = db.Column(db.Integer, primary_key=True)
    sale_number = db.Column(db.String(40), unique=True, nullable=False, index=True)
    user_id = db.Column(db.Integer, db.ForeignKey("users.id"), nullable=False)
    customer_name = db.Column(db.String(120))
    subtotal = db.Column(db.Numeric(12, 2), nullable=False, default=0)
    discount = db.Column(db.Numeric(12, 2), nullable=False, default=0)
    total = db.Column(db.Numeric(12, 2), nullable=False, default=0)
    cost_total = db.Column(db.Numeric(12, 2), nullable=False, default=0)
    gross_profit = db.Column(db.Numeric(12, 2), nullable=False, default=0)
    payment_method = db.Column(db.String(30), nullable=False, default="cash")
    cash_tendered = db.Column(db.Numeric(12, 2), nullable=True)
    change_given = db.Column(db.Numeric(12, 2), nullable=True)
    status = db.Column(db.String(20), default="completed", nullable=False)  # completed/voided/refunded
    idempotency_key = db.Column(db.String(80), unique=True, nullable=True, index=True)
    notes = db.Column(db.String(255))
    created_at = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc), index=True)

    user = db.relationship("User", lazy="joined")
    items = db.relationship("SaleItem", backref="sale", lazy="selectin", cascade="all, delete-orphan")
    payments = db.relationship("Payment", backref="sale", lazy="selectin", cascade="all, delete-orphan")

    def to_dict(self):
        return {
            "id": self.id,
            "sale_number": self.sale_number,
            "user_id": self.user_id,
            "cashier": self.user.full_name if self.user else None,
            "customer_name": self.customer_name,
            "subtotal": float(self.subtotal),
            "discount": float(self.discount),
            "total": float(self.total),
            "cost_total": float(self.cost_total),
            "gross_profit": float(self.gross_profit),
            "payment_method": self.payment_method,
            "cash_tendered": float(self.cash_tendered) if self.cash_tendered is not None else None,
            "change_given": float(self.change_given) if self.change_given is not None else None,
            "status": self.status,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "items": [i.to_dict() for i in self.items],
        }


class SaleItem(db.Model):
    __tablename__ = "sale_items"
    id = db.Column(db.Integer, primary_key=True)
    sale_id = db.Column(db.Integer, db.ForeignKey("sales.id"), nullable=False, index=True)
    product_id = db.Column(db.Integer, db.ForeignKey("products.id"), nullable=True)
    product_name = db.Column(db.String(150), nullable=False)
    sku = db.Column(db.String(80))
    quantity = db.Column(db.Integer, nullable=False)
    unit_cost = db.Column(db.Numeric(12, 2), nullable=False, default=0)
    unit_price = db.Column(db.Numeric(12, 2), nullable=False)
    line_total = db.Column(db.Numeric(12, 2), nullable=False)
    line_cost = db.Column(db.Numeric(12, 2), nullable=False, default=0)
    line_profit = db.Column(db.Numeric(12, 2), nullable=False, default=0)
    created_at = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc))

    product = db.relationship("Product", lazy="joined")

    def to_dict(self):
        return {
            "id": self.id,
            "product_id": self.product_id,
            "product_name": self.product_name,
            "sku": self.sku,
            "quantity": self.quantity,
            "unit_cost": float(self.unit_cost),
            "unit_price": float(self.unit_price),
            "line_total": float(self.line_total),
            "line_cost": float(self.line_cost),
            "line_profit": float(self.line_profit),
        }


class Payment(db.Model):
    __tablename__ = "payments"
    id = db.Column(db.Integer, primary_key=True)
    sale_id = db.Column(db.Integer, db.ForeignKey("sales.id"), nullable=True, index=True)
    debt_id = db.Column(db.Integer, db.ForeignKey("debts.id"), nullable=True, index=True)
    amount = db.Column(db.Numeric(12, 2), nullable=False)
    method = db.Column(db.String(30), nullable=False, default="cash")
    reference = db.Column(db.String(80))
    user_id = db.Column(db.Integer, db.ForeignKey("users.id"), nullable=True)
    created_at = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc), index=True)

    user = db.relationship("User", lazy="joined")
