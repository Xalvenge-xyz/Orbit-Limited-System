from datetime import datetime, timezone
from decimal import Decimal
from backend.extensions import db


class Category(db.Model):
    __tablename__ = "categories"
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), unique=True, nullable=False)
    description = db.Column(db.String(255))
    created_at = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc))

    products = db.relationship("Product", backref="category", lazy="dynamic")


class Product(db.Model):
    __tablename__ = "products"
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(150), nullable=False, index=True)
    sku = db.Column(db.String(80), unique=True, nullable=True, index=True)
    category_id = db.Column(db.Integer, db.ForeignKey("categories.id"), nullable=True)
    supplier_id = db.Column(db.Integer, db.ForeignKey("suppliers.id"), nullable=True)

    cost = db.Column(db.Numeric(12, 2), nullable=False, default=0)
    price = db.Column(db.Numeric(12, 2), nullable=False, default=0)
    min_price = db.Column(db.Numeric(12, 2), nullable=False, default=0)
    target_gross_margin = db.Column(db.Numeric(5, 4), nullable=True)  # e.g. 0.2000

    stock = db.Column(db.Integer, nullable=False, default=0)
    reorder_level = db.Column(db.Integer, nullable=False, default=3)

    status = db.Column(db.String(20), default="active", nullable=False)  # active/archived
    created_at = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc))
    updated_at = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc), onupdate=lambda: datetime.now(timezone.utc))

    supplier = db.relationship("Supplier", backref="products", lazy="joined")

    def is_active(self):
        return self.status == "active"

    def recommended_min_price(self):
        # cost / (1 - margin)
        if self.target_gross_margin is None:
            return None
        m = Decimal(str(self.target_gross_margin))
        if m < 0 or m >= 1:
            return None
        return (Decimal(str(self.cost)) / (Decimal(1) - m)).quantize(Decimal("0.01"))

    def to_dict(self, include_cost=True):
        d = {
            "id": self.id,
            "name": self.name,
            "sku": self.sku,
            "category_id": self.category_id,
            "category_name": self.category.name if self.category else None,
            "supplier_id": self.supplier_id,
            "supplier_name": self.supplier.name if self.supplier else None,
            "price": float(self.price),
            "min_price": float(self.min_price),
            "target_gross_margin": float(self.target_gross_margin) if self.target_gross_margin is not None else None,
            "stock": self.stock,
            "reorder_level": self.reorder_level,
            "status": self.status,
            "created_at": self.created_at.isoformat() if self.created_at else None,
        }
        if include_cost:
            d["cost"] = float(self.cost)
        rec = self.recommended_min_price()
        d["recommended_min_price"] = float(rec) if rec is not None else None
        return d
