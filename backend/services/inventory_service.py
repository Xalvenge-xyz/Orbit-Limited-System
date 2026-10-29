from decimal import Decimal
from backend.extensions import db
from backend.models.product import Product
from backend.models.inventory import StockMovement


class InventoryService:
    @staticmethod
    def adjust_stock(product_id, quantity_change, movement_type, user_id=None,
                    reference_type=None, reference_id=None, reason=None, commit=True):
        product = db.session.get(Product, product_id)
        if not product:
            raise ValueError("Product not found")
        new_stock = product.stock + quantity_change
        if new_stock < 0:
            raise ValueError("Insufficient stock")
        product.stock = new_stock
        movement = StockMovement(
            product_id=product_id,
            quantity_change=quantity_change,
            movement_type=movement_type,
            reference_type=reference_type,
            reference_id=reference_id,
            user_id=user_id,
            reason=reason,
        )
        db.session.add(movement)
        if commit:
            db.session.commit()
        return product

    @staticmethod
    def lock_product(product_id):
        return db.session.query(Product).filter_by(id=product_id).with_for_update().first()
