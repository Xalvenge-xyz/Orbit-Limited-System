from decimal import Decimal
from backend.utils.validators import to_decimal


class PricingService:
    @staticmethod
    def recommended_min_price(cost, target_margin):
        c = to_decimal(cost)
        m = to_decimal(target_margin)
        if c is None or m is None:
            return None
        if m < 0 or m >= 1:
            return None
        return (c / (Decimal(1) - m)).quantize(Decimal("0.01"))

    @staticmethod
    def validate_selected_price(product, selected_price, user):
        # returns (ok, message)
        sp = to_decimal(selected_price)
        if sp is None:
            return False, "Invalid price"
        if sp < Decimal(str(product.min_price)):
            # allow override only if user has permission
            if not user.has_permission("override_price"):
                return False, "Selected price is below the configured minimum"
        if sp <= 0:
            return False, "Price must be positive"
        return True, "ok"
