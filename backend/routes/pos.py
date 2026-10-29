from flask import Blueprint, render_template, request, jsonify
from flask_login import login_required, current_user
from backend.extensions import db
from backend.models.product import Product
from backend.utils.permissions import permission_required
from backend.services.sales_service import SalesService
from backend.utils.validators import to_decimal

pos_bp = Blueprint("pos", __name__, url_prefix="/pos")


@pos_bp.route("/")
@login_required
@permission_required("pos_access")
def index():
    return render_template("pos/index.html")


@pos_bp.route("/api/search")
@login_required
@permission_required("pos_access")
def api_search():
    q = request.args.get("q", "").strip()
    query = Product.query.filter(Product.status == "active")
    if q:
        query = query.filter((Product.name.ilike(f"%{q}%")) | (Product.sku.ilike(f"%{q}%")))
    products = query.order_by(Product.name).limit(100).all()
    include_cost = current_user.has_permission("view_finance")
    out = []
    for p in products:
        out.append({
            "id": p.id,
            "name": p.name,
            "sku": p.sku,
            "price": float(p.price),
            "min_price": float(p.min_price),
            "cost": float(p.cost) if include_cost else None,
            "stock": p.stock,
            "available": p.stock > 0,
        })
    return jsonify(out)


@pos_bp.route("/api/checkout", methods=["POST"])
@login_required
@permission_required("pos_access")
def api_checkout():
    data = request.get_json() or {}
    sale, err = SalesService.checkout(data, current_user)
    if err:
        return jsonify({"error": err}), 400
    return jsonify({"message": "Sale completed", "sale_id": sale.id, "sale_number": sale.sale_number, "total": float(sale.total), "change": float(sale.change_given) if sale.change_given is not None else 0})
