from flask import Blueprint, render_template, request, jsonify
from flask_login import login_required, current_user
from backend.extensions import db
from backend.models.sale import Sale
from backend.utils.permissions import permission_required
from backend.services.reporting_service import ReportingService
from datetime import datetime

sales_bp = Blueprint("sales", __name__, url_prefix="/sales")


@sales_bp.route("/")
@login_required
def index():
    return render_template("sales/index.html")


@sales_bp.route("/receipt/<int:sid>")
@login_required
def receipt(sid):
    sale = db.session.get(Sale, sid)
    if not sale:
        return "Not found", 404
    return render_template("sales/receipt.html", sale=sale)


@sales_bp.route("/api/list")
@login_required
def api_list():
    period = request.args.get("period", "custom")
    start = request.args.get("start")
    end = request.args.get("end")
    s, e = ReportingService.parse_range(period, start, end)
    # cashier only own sales unless view_sales
    q = Sale.query.filter(Sale.created_at >= s, Sale.created_at <= e)
    if not current_user.has_permission("view_sales"):
        q = q.filter_by(user_id=current_user.id)
    status = request.args.get("status")
    if status:
        q = q.filter_by(status=status)
    page = int(request.args.get("page", 1))
    per_page = int(request.args.get("per_page", 20))
    pag = q.order_by(Sale.created_at.desc()).paginate(page=page, per_page=per_page, error_out=False)
    return jsonify({"items": [x.to_dict() for x in pag.items], "total": pag.total, "page": pag.page, "pages": pag.pages})


@sales_bp.route("/api/<int:sid>/void", methods=["POST"])
@login_required
@permission_required("refund_void")
def api_void(sid):
    sale = db.session.get(Sale, sid)
    if not sale or sale.status != "completed":
        return jsonify({"error": "Invalid sale"}), 400
    # reverse stock
    from backend.services.inventory_service import InventoryService
    for it in sale.items:
        if it.product_id:
            InventoryService.adjust_stock(it.product_id, it.quantity, "return", user_id=current_user.id, reference_type="sale", reference_id=sale.id, reason=f"Void {sale.sale_number}", commit=False)
    sale.status = "voided"
    db.session.commit()
    from backend.utils.audit import log_action
    log_action(current_user.id, "sale_voided", "sale", sale.id, sale.sale_number)
    return jsonify({"message": "Sale voided"})
