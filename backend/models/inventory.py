from datetime import datetime, timezone
from backend.extensions import db


class StockMovement(db.Model):
    __tablename__ = "stock_movements"
    id = db.Column(db.Integer, primary_key=True)
    product_id = db.Column(db.Integer, db.ForeignKey("products.id"), nullable=False, index=True)
    quantity_change = db.Column(db.Integer, nullable=False)  # positive in, negative out
    movement_type = db.Column(db.String(40), nullable=False)  # opening/purchase/sale/return/adjustment
    reference_type = db.Column(db.String(40))  # sale/purchase/adjustment
    reference_id = db.Column(db.Integer)
    user_id = db.Column(db.Integer, db.ForeignKey("users.id"), nullable=True)
    reason = db.Column(db.String(255))
    created_at = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc), index=True)

    product = db.relationship("Product", lazy="joined")
    user = db.relationship("User", lazy="joined")
