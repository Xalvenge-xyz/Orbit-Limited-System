from flask import Blueprint, render_template, request, jsonify
from flask_login import login_required, current_user
from backend.extensions import db
from backend.models.product import Product
from backend.models.inventory import StockMovement
from backend.utils.permissions import permission_required
from backend.utils.validators import positive_int, to_decimal
from backend.services.inventory_service import InventoryService
from backend.utils.audit import log_action

inventory_bp = Blueprint("inventory", __name__, url_prefix="/inventory")


@inventory_bp.route("/")
@login_required
def index():
    return render_template("inventory/index.html")


@inventory_bp.route("/api/movements")
@login_required
def api_movements():
    q = StockMovement.query
    product_id = request.args.get("product_id")
    if product_id:
        q = q.filter_by(product_id=int(product_id))
    mtype = request.args.get("type")
    if mtype:
        q = q.filter_by(movement_type=mtype)
    page = int(request.args.get("page", 1))
    per_page = int(request.args.get("per_page", 30))
    pag = q.order_by(StockMovement.created_at.desc()).paginate(page=page, per_page=per_page, error_out=False)
    items = []
    for m in pag.items:
        items.append({
            "id": m.id,
            "product_id": m.product_id,
            "product_name": m.product.name if m.product else None,
            "quantity_change": m.quantity_change,
            "movement_type": m.movement_type,
            "reference_type": m.reference_type,
            "reference_id": m.reference_id,
            "user": m.user.full_name if m.user else None,
            "reason": m.reason,
            "created_at": m.created_at.isoformat() if m.created_at else None,
        })
    return jsonify({"items": items, "total": pag.total, "page": pag.page, "pages": pag.pages})


@inventory_bp.route("/api/adjust", methods=["POST"])
@login_required
@permission_required("manage_inventory")
def api_adjust():
    data = request.get_json() or {}
    try:
        pid = int(data.get("product_id"))
    except (ValueError, TypeError):
        return jsonify({"error": "Invalid product"}), 400
    qty = data.get("quantity_change")
    try:
        qty = int(qty)
    except (ValueError, TypeError):
        return jsonify({"error": "Invalid quantity"}), 400
    if qty == 0:
        return jsonify({"error": "Quantity cannot be zero"}), 400
    mtype = data.get("movement_type", "adjustment")
    reason = (data.get("reason") or "").strip() or "Manual adjustment"
    try:
        InventoryService.adjust_stock(pid, qty, mtype, user_id=current_user.id, reason=reason, commit=True)
    except ValueError as e:
        return jsonify({"error": str(e)}), 400
    log_action(current_user.id, "stock_adjusted", "product", pid, f"{qty} {reason}")
    return jsonify({"message": "Stock adjusted"})


@inventory_bp.route("/api/low-stock")
@login_required
def api_low_stock():
    from backend.services.notification_service import NotificationService
    items = NotificationService.low_stock_products()
    return jsonify([{"id": p.id, "name": p.name, "stock": p.stock, "reorder_level": p.reorder_level} for p in items])
