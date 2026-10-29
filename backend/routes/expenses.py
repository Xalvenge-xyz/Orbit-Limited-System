from flask import Blueprint, render_template, request, jsonify
from flask_login import login_required, current_user
from backend.extensions import db
from backend.models.expense import Expense, ExpenseCategory
from backend.utils.permissions import permission_required
from backend.utils.validators import to_decimal
from backend.utils.audit import log_action
from datetime import datetime, date

expenses_bp = Blueprint("expenses", __name__, url_prefix="/expenses")


@expenses_bp.route("/")
@login_required
def index():
    return render_template("expenses/index.html")


@expenses_bp.route("/api/categories")
@login_required
def api_categories():
    cats = ExpenseCategory.query.order_by(ExpenseCategory.name).all()
    if not cats:
        # seed defaults
        for n in ["Rent", "Utilities", "Salaries", "Supplies", "Transportation", "Marketing", "Other"]:
            db.session.add(ExpenseCategory(name=n))
        db.session.commit()
        cats = ExpenseCategory.query.order_by(ExpenseCategory.name).all()
    return jsonify([{"id": c.id, "name": c.name} for c in cats])


@expenses_bp.route("/api/list")
@login_required
def api_list():
    q = Expense.query
    cat = request.args.get("category_id")
    if cat:
        q = q.filter_by(category_id=int(cat))
    start = request.args.get("start")
    end = request.args.get("end")
    if start:
        q = q.filter(Expense.expense_date >= datetime.fromisoformat(start).date())
    if end:
        q = q.filter(Expense.expense_date <= datetime.fromisoformat(end).date())
    page = int(request.args.get("page", 1))
    per_page = int(request.args.get("per_page", 20))
    pag = q.order_by(Expense.expense_date.desc()).paginate(page=page, per_page=per_page, error_out=False)
    items = []
    for e in pag.items:
        items.append({
            "id": e.id,
            "description": e.description,
            "category_id": e.category_id,
            "category_name": e.category.name if e.category else None,
            "amount": float(e.amount),
            "expense_date": e.expense_date.isoformat(),
            "payment_method": e.payment_method,
            "notes": e.notes,
            "status": e.status,
            "user": e.user.full_name if e.user else None,
        })
    return jsonify({"items": items, "total": pag.total, "page": pag.page, "pages": pag.pages})


@expenses_bp.route("/api/create", methods=["POST"])
@login_required
@permission_required("manage_expenses")
def api_create():
    data = request.get_json() or {}
    desc = (data.get("description") or "").strip()
    if not desc:
        return jsonify({"error": "Description required"}), 400
    amt = to_decimal(data.get("amount"))
    if amt is None or amt <= 0:
        return jsonify({"error": "Invalid amount"}), 400
    try:
        edate = datetime.fromisoformat(data.get("expense_date")).date() if data.get("expense_date") else date.today()
    except Exception:
        edate = date.today()
    cat_id = data.get("category_id") or None
    e = Expense(
        description=desc,
        category_id=int(cat_id) if cat_id else None,
        amount=amt,
        expense_date=edate,
        payment_method=data.get("payment_method", "cash"),
        notes=data.get("notes"),
        user_id=current_user.id,
        status="recorded",
    )
    db.session.add(e)
    db.session.commit()
    log_action(current_user.id, "expense_created", "expense", e.id, desc)
    return jsonify({"message": "Expense saved", "id": e.id})


@expenses_bp.route("/api/<int:eid>/void", methods=["POST"])
@login_required
@permission_required("manage_expenses")
def api_void(eid):
    e = db.session.get(Expense, eid)
    if not e:
        return jsonify({"error": "Not found"}), 404
    e.status = "voided"
    db.session.commit()
    log_action(current_user.id, "expense_voided", "expense", e.id, e.description)
    return jsonify({"message": "Expense voided"})
