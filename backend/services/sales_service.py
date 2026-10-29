import uuid
from datetime import datetime, timezone
from decimal import Decimal
from backend.extensions import db
from backend.models.product import Product
from backend.models.sale import Sale, SaleItem, Payment
from backend.utils.validators import to_decimal, positive_int
from backend.services.inventory_service import InventoryService
from backend.utils.audit import log_action


class SalesService:
    @staticmethod
    def generate_sale_number():
        return "S-" + datetime.now(timezone.utc).strftime("%Y%m%d") + "-" + uuid.uuid4().hex[:6].upper()

    @staticmethod
    def checkout(payload, user):
        idem = payload.get("idempotency_key")
        if idem:
            existing = Sale.query.filter_by(idempotency_key=idem).first()
            if existing:
                return existing, None

        items = payload.get("items") or []
        if not items:
            return None, "Cart is empty"

        payment_method = payload.get("payment_method", "cash")
        if payment_method not in ("cash", "card", "gcash", "bank"):
            return None, "Invalid payment method"

        cash_tendered = to_decimal(payload.get("cash_tendered"))
        customer_name = (payload.get("customer_name") or "").strip() or None

        normalized = []
        for it in items:
            try:
                pid = int(it.get("product_id"))
            except (ValueError, TypeError):
                return None, "Invalid product"
            qty = positive_int(it.get("quantity"))
            if qty is None:
                return None, "Invalid quantity"
            selected_price = to_decimal(it.get("selected_price"))
            if selected_price is None or selected_price <= 0:
                return None, "Invalid selected price"
            normalized.append({"product_id": pid, "quantity": qty, "selected_price": selected_price})

        try:
            product_ids = [n["product_id"] for n in normalized]
            products = {}
            for pid in product_ids:
                p = InventoryService.lock_product(pid)
                if not p:
                    raise ValueError("Product not found")
                if p.status != "active":
                    raise ValueError(f"Product {p.name} is not available")
                products[pid] = p

            for n in normalized:
                p = products[n["product_id"]]
                if n["quantity"] > p.stock:
                    raise ValueError(f"Insufficient stock for {p.name}")
                if n["selected_price"] < Decimal(str(p.min_price)):
                    if not user.has_permission("override_price"):
                        raise ValueError(f"Price below minimum for {p.name}")

            subtotal = Decimal("0")
            cost_total = Decimal("0")
            line_items_data = []
            for n in normalized:
                p = products[n["product_id"]]
                qty = n["quantity"]
                price = n["selected_price"]
                line_total = (Decimal(qty) * price).quantize(Decimal("0.01"))
                line_cost = (Decimal(qty) * Decimal(str(p.cost))).quantize(Decimal("0.01"))
                line_profit = (line_total - line_cost).quantize(Decimal("0.01"))
                subtotal += line_total
                cost_total += line_cost
                line_items_data.append((p, qty, price, line_total, line_cost, line_profit))

            discount = Decimal("0")
            total = (subtotal - discount).quantize(Decimal("0.01"))
            gross_profit = (total - cost_total).quantize(Decimal("0.01"))

            change_given = None
            if payment_method == "cash":
                if cash_tendered is None:
                    raise ValueError("Cash tendered required")
                if cash_tendered < total:
                    raise ValueError("Insufficient cash tendered")
                change_given = (cash_tendered - total).quantize(Decimal("0.01"))

            sale = Sale(
                sale_number=SalesService.generate_sale_number(),
                user_id=user.id,
                customer_name=customer_name,
                subtotal=subtotal,
                discount=discount,
                total=total,
                cost_total=cost_total,
                gross_profit=gross_profit,
                payment_method=payment_method,
                cash_tendered=cash_tendered if payment_method == "cash" else None,
                change_given=change_given,
                status="completed",
                idempotency_key=idem,
            )
            db.session.add(sale)
            db.session.flush()

            for (p, qty, price, line_total, line_cost, line_profit) in line_items_data:
                si = SaleItem(
                    sale_id=sale.id,
                    product_id=p.id,
                    product_name=p.name,
                    sku=p.sku,
                    quantity=qty,
                    unit_cost=Decimal(str(p.cost)),
                    unit_price=price,
                    line_total=line_total,
                    line_cost=line_cost,
                    line_profit=line_profit,
                )
                db.session.add(si)

            pay = Payment(sale_id=sale.id, amount=total, method=payment_method, user_id=user.id)
            db.session.add(pay)

            for (p, qty, price, line_total, line_cost, line_profit) in line_items_data:
                InventoryService.adjust_stock(
                    p.id, -qty, "sale", user_id=user.id,
                    reference_type="sale", reference_id=sale.id,
                    reason=f"Sale {sale.sale_number}", commit=False,
                )

            db.session.commit()
            log_action(user.id, "sale_completed", "sale", sale.id, f"Total {total}")
            return sale, None

        except Exception as e:
            db.session.rollback()
            return None, str(e)
