from flask import Blueprint, render_template, request, jsonify
from flask_login import login_required, current_user
from backend.extensions import db
from backend.models.budget import Budget
from backend.models.product import Product, Category
from backend.models.supplier import Supplier
from backend.models.expense import Expense, ExpenseCategory
from backend.models.capital import CapitalTransaction
from backend.models.debt import Debt, DebtPayment
from backend.models.purchase import Purchase, PurchaseItem
from backend.models.sale import Sale, SaleItem, Payment
from backend.models.inventory import StockMovement
from backend.models.employee import Employee
from backend.models.audit_log import AuditLog
from backend.utils.permissions import permission_required
from backend.utils.validators import to_decimal
from backend.utils.audit import log_action

settings_bp = Blueprint("settings", __name__, url_prefix="/settings")


@settings_bp.route("/")
@login_required
def index():
    return render_template("settings/index.html")


@settings_bp.route("/api/profile", methods=["GET"])
@login_required
def api_profile_get():
    return jsonify({
        "full_name": current_user.full_name,
        "email": current_user.email,
        "mobile": current_user.mobile,
        "role": current_user.role_name(),
    })


@settings_bp.route("/api/profile", methods=["POST"])
@login_required
def api_profile_update():
    data = request.get_json() or {}
    if "full_name" in data and data["full_name"].strip():
        current_user.full_name = data["full_name"].strip()
    if "mobile" in data:
        current_user.mobile = (data["mobile"] or "").strip()
    if "email" in data and data["email"].strip():
        new_email = data["email"].strip().lower()
        if new_email != current_user.email:
            from backend.models.user import User
            if User.query.filter_by(email=new_email).first():
                return jsonify({"error": "Email already in use"}), 400
            current_user.email = new_email
    db.session.commit()
    log_action(current_user.id, "profile_updated", "user", current_user.id, "")
    return jsonify({"message": "Profile updated"})


@settings_bp.route("/api/change-password", methods=["POST"])
@login_required
def api_change_password():
    data = request.get_json() or {}
    current_pw = data.get("current_password", "")
    new_pw = data.get("new_password", "")
    confirm = data.get("confirm_password", "")
    if not current_user.check_password(current_pw):
        return jsonify({"error": "Current password is incorrect"}), 400
    if new_pw != confirm or len(new_pw) < 8:
        return jsonify({"error": "New passwords must match and be at least 8 characters"}), 400
    current_user.set_password(new_pw)
    db.session.commit()
    log_action(current_user.id, "password_changed", "user", current_user.id, "")
    return jsonify({"message": "Password changed"})


@settings_bp.route("/api/wipe-data", methods=["POST"])
@login_required
@permission_required("manage_settings")
def api_wipe_data():
    if current_user.role_name() != "owner":
        return jsonify({"error": "Only the owner can wipe data"}), 403
    data = request.get_json() or {}
    if data.get("confirm") != "WIPE":
        return jsonify({"error": "Type WIPE to confirm"}), 400
    if not current_user.check_password(data.get("password", "")):
        return jsonify({"error": "Incorrect password"}), 400
    try:
        AuditLog.query.delete()
        DebtPayment.query.delete()
        Debt.query.delete()
        Payment.query.delete()
        SaleItem.query.delete()
        Sale.query.delete()
        PurchaseItem.query.delete()
        Purchase.query.delete()
        StockMovement.query.delete()
        Expense.query.delete()
        ExpenseCategory.query.delete()
        CapitalTransaction.query.delete()
        Budget.query.delete()
        Employee.query.delete()
        Product.query.delete()
        Category.query.delete()
        Supplier.query.delete()
        db.session.commit()
        log_action(current_user.id, "data_wiped", "system", None, "All business data wiped")
        return jsonify({"message": "All business data wiped"})
    except Exception as e:
        db.session.rollback()
        return jsonify({"error": str(e)}), 500


@settings_bp.route("/api/categories")
@login_required
def api_categories():
    cats = Category.query.order_by(Category.name).all()
    return jsonify([{"id": c.id, "name": c.name, "description": c.description} for c in cats])

@settings_bp.route("/api/categories", methods=["POST"])
@login_required
@permission_required("manage_settings")
def api_category_create():
    data = request.get_json() or {}
    name = (data.get("name") or "").strip()
    if not name:
        return jsonify({"error": "Name required"}), 400
    if Category.query.filter_by(name=name).first():
        return jsonify({"error": "Exists"}), 400
    c = Category(name=name, description=data.get("description"))
    db.session.add(c)
    db.session.commit()
    return jsonify({"message": "Created", "id": c.id})


@settings_bp.route("/api/expense-categories")
@login_required
def api_expense_categories():
    cats = ExpenseCategory.query.order_by(ExpenseCategory.name).all()
    return jsonify([{"id": c.id, "name": c.name} for c in cats])


@settings_bp.route("/api/budgets")
@login_required
def api_budgets():
    items = Budget.query.order_by(Budget.created_at.desc()).all()
    return jsonify([{
        "id": b.id,
        "name": b.name,
        "category": b.category,
        "amount": float(b.amount),
        "period_start": b.period_start.isoformat() if b.period_start else None,
        "period_end": b.period_end.isoformat() if b.period_end else None,
        "safe_spend_percent": b.safe_spend_percent,
    } for b in items])


@settings_bp.route("/api/budgets", methods=["POST"])
@login_required
@permission_required("manage_settings")
def api_budget_create():
    data = request.get_json() or {}
    name = (data.get("name") or "").strip()
    if not name:
        return jsonify({"error": "Name required"}), 400
    amt = to_decimal(data.get("amount"))
    if amt is None:
        amt = 0
    from datetime import datetime
    ps = None
    pe = None
    if data.get("period_start"):
        try:
            ps = datetime.fromisoformat(data["period_start"]).date()
        except Exception:
            ps = None
    if data.get("period_end"):
        try:
            pe = datetime.fromisoformat(data["period_end"]).date()
        except Exception:
            pe = None
    b = Budget(
        name=name,
        category=data.get("category"),
        amount=amt,
        period_start=ps,
        period_end=pe,
        safe_spend_percent=int(data.get("safe_spend_percent", 30)),
        user_id=current_user.id,
    )
    db.session.add(b)
    db.session.commit()
    return jsonify({"message": "Budget saved", "id": b.id})
