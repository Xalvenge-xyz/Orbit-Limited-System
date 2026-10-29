from flask import Blueprint, render_template, request, jsonify, flash
from flask_login import login_required, current_user
from backend.extensions import db
from backend.models.product import Product, Category
from backend.models.supplier import Supplier
from backend.utils.permissions import permission_required
from backend.utils.validators import to_decimal, positive_int
from backend.utils.audit import log_action
from backend.services.pricing_service import PricingService

products_bp = Blueprint("products", __name__, url_prefix="/products")


@products_bp.route("/")
@login_required
def index():
    return render_template("products/index.html")


@products_bp.route("/api/list")
@login_required
def api_list():
    q = Product.query
    search = request.args.get("search", "").strip()
    if search:
        q = q.filter((Product.name.ilike(f"%{search}%")) | (Product.sku.ilike(f"%{search}%")))
    category_id = request.args.get("category_id")
    if category_id:
        q = q.filter_by(category_id=int(category_id))
    status = request.args.get("status")
    if status:
        q = q.filter_by(status=status)
    stock_status = request.args.get("stock_status")
    if stock_status == "low":
        q = q.filter(Product.stock <= 3)
    elif stock_status == "out":
        q = q.filter(Product.stock <= 0)
    page = int(request.args.get("page", 1))
    per_page = int(request.args.get("per_page", 20))
    pag = q.order_by(Product.name).paginate(page=page, per_page=per_page, error_out=False)
    include_cost = current_user.has_permission("view_finance") or current_user.has_permission("manage_products")
    return jsonify({
        "items": [p.to_dict(include_cost=include_cost) for p in pag.items],
        "total": pag.total,
        "page": pag.page,
        "pages": pag.pages,
    })


@products_bp.route("/api/categories")
@login_required
def api_categories():
    cats = Category.query.order_by(Category.name).all()
    return jsonify([{"id": c.id, "name": c.name} for c in cats])


@products_bp.route("/api/suppliers")
@login_required
def api_suppliers():
    sups = Supplier.query.order_by(Supplier.name).all()
    return jsonify([{"id": s.id, "name": s.name} for s in sups])


@products_bp.route("/api/create", methods=["POST"])
@login_required
@permission_required("manage_products")
def api_create():
    data = request.get_json() or {}
    name = (data.get("name") or "").strip()
    if not name:
        return jsonify({"error": "Name required"}), 400
    sku = (data.get("sku") or "").strip() or None
    if sku and Product.query.filter_by(sku=sku).first():
        return jsonify({"error": "SKU already exists"}), 400
    cost = to_decimal(data.get("cost"))
    price = to_decimal(data.get("price"))
    min_price = to_decimal(data.get("min_price"))
    if cost is None or price is None or min_price is None:
        return jsonify({"error": "Invalid prices"}), 400
    margin = data.get("target_gross_margin")
    margin = to_decimal(margin) if margin not in (None, "") else None
    if margin is not None and (margin < 0 or margin >= 1):
        return jsonify({"error": "Invalid target margin"}), 400
    # resolve category
    cat_id = data.get("category_id")
    cat_name = (data.get("category") or data.get("category_name") or "").strip()
    if not cat_id and cat_name:
        from backend.models.product import Category
        c = Category.query.filter_by(name=cat_name).first()
        if not c:
            c = Category(name=cat_name)
            db.session.add(c)
            db.session.flush()
        cat_id = c.id
    # resolve supplier
    sup_id = data.get("supplier_id")
    sup_name = (data.get("supplier") or data.get("supplier_name") or "").strip()
    if not sup_id and sup_name:
        from backend.models.supplier import Supplier
        s = Supplier.query.filter_by(name=sup_name).first()
        if not s:
            s = Supplier(name=sup_name)
            db.session.add(s)
            db.session.flush()
        sup_id = s.id
    stock = positive_int(data.get("stock"))
    if stock is None:
        stock = 0
    reorder = positive_int(data.get("reorder_level"))
    if reorder is None:
        reorder = 3
    p = Product(
        name=name, sku=sku,
        category_id=int(cat_id) if cat_id else None,
        supplier_id=int(sup_id) if sup_id else None,
        cost=cost, price=price, min_price=min_price,
        target_gross_margin=margin,
        stock=stock, reorder_level=reorder, status="active",
    )
    db.session.add(p)
    db.session.commit()
    if stock > 0:
        from backend.models.inventory import StockMovement
        mv = StockMovement(product_id=p.id, quantity_change=stock, movement_type="opening", user_id=current_user.id, reason="Initial stock")
        db.session.add(mv)
        db.session.commit()
    log_action(current_user.id, "product_created", "product", p.id, name)
    return jsonify({"message": "Product created", "id": p.id})


@products_bp.route("/api/<int:pid>", methods=["GET"])
@login_required
def api_get(pid):
    p = db.session.get(Product, pid)
    if not p:
        return jsonify({"error": "Not found"}), 404
    include_cost = current_user.has_permission("view_finance") or current_user.has_permission("manage_products")
    return jsonify(p.to_dict(include_cost=include_cost))


@products_bp.route("/api/<int:pid>/update", methods=["POST"])
@login_required
@permission_required("manage_products")
def api_update(pid):
    p = db.session.get(Product, pid)
    if not p:
        return jsonify({"error": "Not found"}), 404
    data = request.get_json() or {}
    if "name" in data and data["name"]:
        p.name = data["name"].strip()
    if "sku" in data:
        sku = (data["sku"] or "").strip() or None
        if sku and sku != p.sku and Product.query.filter_by(sku=sku).first():
            return jsonify({"error": "SKU exists"}), 400
        p.sku = sku
    if "cost" in data and data["cost"] not in (None, ""):
        p.cost = to_decimal(data["cost"])
    if "price" in data and data["price"] not in (None, ""):
        p.price = to_decimal(data["price"])
    if "min_price" in data and data["min_price"] not in (None, ""):
        p.min_price = to_decimal(data["min_price"])
    if "target_gross_margin" in data:
        m = data["target_gross_margin"]
        p.target_gross_margin = to_decimal(m) if m not in (None, "") else None
    if "category" in data or "category_name" in data or "category_id" in data:
        cat_id = data.get("category_id")
        cat_name = (data.get("category") or data.get("category_name") or "").strip()
        if not cat_id and cat_name:
            from backend.models.product import Category
            c = Category.query.filter_by(name=cat_name).first()
            if not c:
                c = Category(name=cat_name)
                db.session.add(c)
                db.session.flush()
            cat_id = c.id
        p.category_id = int(cat_id) if cat_id else None
    if "supplier" in data or "supplier_name" in data or "supplier_id" in data:
        sup_id = data.get("supplier_id")
        sup_name = (data.get("supplier") or data.get("supplier_name") or "").strip()
        if not sup_id and sup_name:
            from backend.models.supplier import Supplier
            s = Supplier.query.filter_by(name=sup_name).first()
            if not s:
                s = Supplier(name=sup_name)
                db.session.add(s)
                db.session.flush()
            sup_id = s.id
        p.supplier_id = int(sup_id) if sup_id else None
    if "reorder_level" in data:
        r = positive_int(data["reorder_level"])
        if r is not None:
            p.reorder_level = r
    if "stock" in data:
        new_stock = positive_int(data["stock"])
        if new_stock is None:
            new_stock = 0
        if new_stock != p.stock:
            diff = new_stock - p.stock
            p.stock = new_stock
            from backend.models.inventory import StockMovement
            mv = StockMovement(product_id=p.id, quantity_change=diff, movement_type="adjustment", user_id=current_user.id, reason="Manual edit")
            db.session.add(mv)
    if "status" in data:
        p.status = data["status"]
    db.session.commit()
    log_action(current_user.id, "product_updated", "product", p.id, p.name)
    return jsonify({"message": "Product updated"})


@products_bp.route("/api/<int:pid>/archive", methods=["POST"])
@login_required
@permission_required("manage_products")
def api_archive(pid):
    p = db.session.get(Product, pid)
    if not p:
        return jsonify({"error": "Not found"}), 404
    p.status = "archived"
    db.session.commit()
    log_action(current_user.id, "product_archived", "product", p.id, p.name)
    return jsonify({"message": "Product archived"})


@products_bp.route("/api/recommended-price", methods=["POST"])
@login_required
def api_recommended():
    data = request.get_json() or {}
    cost = to_decimal(data.get("cost"))
    margin = to_decimal(data.get("margin"))
    rec = PricingService.recommended_min_price(cost, margin)
    if rec is None:
        return jsonify({"error": "Invalid input"}), 400
    return jsonify({"recommended": float(rec)})
