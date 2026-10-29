from flask import Blueprint, render_template, request, jsonify
from flask_login import login_required, current_user
from backend.extensions import db
from backend.models.purchase import Purchase, PurchaseItem
from backend.models.product import Product
from backend.models.supplier import Supplier
from backend.models.debt import Debt
from backend.utils.permissions import permission_required
from backend.utils.validators import to_decimal, positive_int
from backend.services.inventory_service import InventoryService
from backend.utils.audit import log_action
from datetime import datetime, date
from decimal import Decimal

purchases_bp = Blueprint("purchases", __name__, url_prefix="/purchases")


@purchases_bp.route("/")
@login_required
def index():
    return render_template("purchases/index.html")


@purchases_bp.route("/api/list")
@login_required
def api_list():
    q = Purchase.query
    page = int(request.args.get("page", 1))
    per_page = int(request.args.get("per_page", 20))
    pag = q.order_by(Purchase.created_at.desc()).paginate(page=page, per_page=per_page, error_out=False)
    items = []
    for p in pag.items:
        items.append({
            "id": p.id,
            "supplier_id": p.supplier_id,
            "supplier_name": p.supplier.name if p.supplier else None,
            "reference": p.reference,
            "total": float(p.total),
            "amount_paid": float(p.amount_paid),
            "payment_status": p.payment_status,
            "notes": p.notes,
            "created_at": p.created_at.isoformat(),
            "items": [{"product_id": i.product_id, "product_name": i.product.name if i.product else None, "quantity": i.quantity, "unit_cost": float(i.unit_cost), "line_total": float(i.line_total)} for i in p.items],
        })
    return jsonify({"items": items, "total": pag.total, "page": pag.page, "pages": pag.pages})


@purchases_bp.route("/api/create", methods=["POST"])
@login_required
@permission_required("manage_purchases")
def api_create():
    data = request.get_json() or {}
    items = data.get("items") or []
    # items are optional; if none provided, record as a simple purchase amount
    # resolve supplier
    supplier_id = data.get("supplier_id")
    supplier_name = (data.get("supplier") or data.get("supplier_name") or "").strip()
    if not supplier_id and supplier_name:
        from backend.models.supplier import Supplier
        s = Supplier.query.filter_by(name=supplier_name).first()
        if not s:
            s = Supplier(name=supplier_name)
            db.session.add(s)
            db.session.flush()
        supplier_id = s.id
    try:
        total = Decimal(0)
        if not items:
            total = Decimal(str(data.get("amount_paid", 0) or 0))
        purchase = Purchase(
            supplier_id=int(supplier_id) if supplier_id else None,
            reference=(data.get("reference") or "").strip(),
            notes=data.get("notes"),
            amount_paid=Decimal(str(data.get("amount_paid", 0) or 0)),
            user_id=current_user.id,
        )
        db.session.add(purchase)
        db.session.flush()
        for it in items:
            if not it:
                continue
            pid = it.get("product_id")
            if not pid and it.get("product_name"):
                # create new product
                from backend.models.product import Product
                name = (it.get("product_name") or "").strip()
                if not name:
                    raise ValueError("Product name required")
                cost = to_decimal(it.get("unit_cost")) or Decimal(0)
                price = to_decimal(it.get("price")) or (cost * Decimal("1.25"))
                min_price = to_decimal(it.get("min_price")) or cost
                cat_name = (it.get("category") or "").strip()
                cat_id = None
                if cat_name:
                    from backend.models.product import Category
                    c = Category.query.filter_by(name=cat_name).first()
                    if not c:
                        c = Category(name=cat_name)
                        db.session.add(c)
                        db.session.flush()
                    cat_id = c.id
                p = Product(name=name, category_id=cat_id, cost=cost, price=price, min_price=min_price, stock=0, status="active")
                db.session.add(p)
                db.session.flush()
                pid = p.id
            pid = int(pid)
            qty = positive_int(it["quantity"])
            if qty is None:
                raise ValueError("Invalid quantity")
            uc = to_decimal(it["unit_cost"])
            if uc is None or uc < 0:
                raise ValueError("Invalid cost")
            line = (Decimal(qty) * uc).quantize(Decimal("0.01"))
            total += line
            pi = PurchaseItem(purchase_id=purchase.id, product_id=pid, quantity=qty, unit_cost=uc, line_total=line)
            db.session.add(pi)
            InventoryService.adjust_stock(pid, qty, "purchase", user_id=current_user.id, reference_type="purchase", reference_id=purchase.id, reason=f"Purchase #{purchase.id}", commit=False)
            # update product cost to latest purchase cost
            prod = db.session.get(Product, pid)
            if prod:
                prod.cost = uc
        purchase.total = total
        ap = Decimal(str(data.get("amount_paid", 0) or 0))
        if ap < 0:
            return jsonify({"error": "Amount paid cannot be negative"}), 400
        purchase.amount_paid = ap
        if total <= 0:
            return jsonify({"error": "Purchase amount must be greater than zero"}), 400
        if ap >= total and total > 0:
            purchase.payment_status = "paid"
        elif ap > 0:
            purchase.payment_status = "partial"
        else:
            purchase.payment_status = "unpaid"
        db.session.commit()
        # create payable debt if unpaid balance
        balance = total - ap
        if balance > 0 and supplier_id:
            sup = db.session.get(Supplier, int(supplier_id))
            name = sup.name if sup else "Supplier"
            DebtService_create = None
            from backend.services.debt_service import DebtService
            DebtService.create_debt(
                name=name, debt_type="payable", amount=balance,
                debt_date=date.today(), notes=f"Purchase #{purchase.id}",
                supplier_id=int(supplier_id), user_id=current_user.id,
                reference_type="purchase", reference_id=purchase.id,
            )
        log_action(current_user.id, "purchase_created", "purchase", purchase.id, str(total))
        return jsonify({"message": "Purchase recorded", "id": purchase.id, "total": float(total)})
    except Exception as e:
        db.session.rollback()
        return jsonify({"error": str(e)}), 400


@purchases_bp.route("/api/<int:pid>/update", methods=["POST"])
@login_required
@permission_required("manage_purchases")
def api_update(pid):
    purchase = db.session.get(Purchase, pid)
    if not purchase:
        return jsonify({"error": "Not found"}), 404
    data = request.get_json() or {}
    if "reference" in data:
        purchase.reference = (data.get("reference") or "").strip()
    if "amount_paid" in data:
        ap = to_decimal(data.get("amount_paid"))
        if ap is None or ap <= 0:
            return jsonify({"error": "Amount paid must be greater than zero"}), 400
        purchase.amount_paid = ap
        if ap >= purchase.total:
            purchase.payment_status = "paid"
        else:
            purchase.payment_status = "partial"
    if "notes" in data:
        purchase.notes = data.get("notes")
    db.session.commit()
    log_action(current_user.id, "purchase_updated", "purchase", purchase.id, str(purchase.total))
    return jsonify({"message": "Purchase updated"})


@purchases_bp.route("/api/<int:pid>/delete", methods=["POST"])
@login_required
@permission_required("manage_purchases")
def api_delete(pid):
    purchase = db.session.get(Purchase, pid)
    if not purchase:
        return jsonify({"error": "Not found"}), 404
    for it in purchase.items:
        if it.product_id:
            InventoryService.adjust_stock(it.product_id, -it.quantity, "adjustment", user_id=current_user.id, reference_type="purchase", reference_id=purchase.id, reason=f"Delete purchase #{purchase.id}", commit=False)
    from backend.models.debt import Debt
    debts = Debt.query.filter_by(reference_type="purchase", reference_id=purchase.id).all()
    for d in debts:
        db.session.delete(d)
    db.session.delete(purchase)
    db.session.commit()
    log_action(current_user.id, "purchase_deleted", "purchase", pid, "")
    return jsonify({"message": "Purchase deleted"})
