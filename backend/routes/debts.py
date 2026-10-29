from flask import Blueprint, render_template, request, jsonify
from flask_login import login_required, current_user
from backend.extensions import db
from backend.models.debt import Debt, DebtPayment
from backend.models.supplier import Supplier
from backend.utils.permissions import permission_required
from backend.utils.validators import to_decimal
from backend.services.debt_service import DebtService
from backend.utils.audit import log_action
from datetime import datetime, date

debts_bp = Blueprint("debts", __name__, url_prefix="/debts")


@debts_bp.route("/")
@login_required
def index():
    return render_template("debts/index.html")


@debts_bp.route("/api/list")
@login_required
def api_list():
    q = Debt.query
    dtype = request.args.get("type")
    if dtype:
        q = q.filter_by(debt_type=dtype)
    status = request.args.get("status")
    if status:
        q = q.filter_by(status=status)
    start = request.args.get("start")
    end = request.args.get("end")
    if start:
        q = q.filter(Debt.debt_date >= datetime.fromisoformat(start).date())
    if end:
        q = q.filter(Debt.debt_date <= datetime.fromisoformat(end).date())
    page = int(request.args.get("page", 1))
    per_page = int(request.args.get("per_page", 20))
    pag = q.order_by(Debt.debt_date.desc()).paginate(page=page, per_page=per_page, error_out=False)
    items = []
    for d in pag.items:
        items.append({
            "id": d.id,
            "name": d.name,
            "debt_type": d.debt_type,
            "amount": float(d.amount),
            "paid_amount": float(d.paid_amount),
            "balance": float(d.balance),
            "status": d.status,
            "debt_date": d.debt_date.isoformat(),
            "due_date": d.due_date.isoformat() if d.due_date else None,
            "notes": d.notes,
            "supplier_id": d.supplier_id,
        })
    return jsonify({"items": items, "total": pag.total, "page": pag.page, "pages": pag.pages})


@debts_bp.route("/api/create", methods=["POST"])
@login_required
@permission_required("manage_debts")
def api_create():
    data = request.get_json() or {}
    name = (data.get("name") or "").strip()
    if not name:
        return jsonify({"error": "Name required"}), 400
    dtype = data.get("debt_type")
    if dtype not in ("receivable", "payable"):
        return jsonify({"error": "Invalid type"}), 400
    amt = to_decimal(data.get("amount"))
    if amt is None or amt <= 0:
        return jsonify({"error": "Invalid amount"}), 400
    try:
        ddate = datetime.fromisoformat(data.get("debt_date")).date() if data.get("debt_date") else date.today()
    except Exception:
        ddate = date.today()
    due = None
    if data.get("due_date"):
        try:
            due = datetime.fromisoformat(data["due_date"]).date()
        except Exception:
            due = None
    d = DebtService.create_debt(
        name=name, debt_type=dtype, amount=amt, debt_date=ddate, due_date=due,
        notes=data.get("notes"), supplier_id=data.get("supplier_id"),
        user_id=current_user.id,
    )
    log_action(current_user.id, "debt_created", "debt", d.id, name)
    return jsonify({"message": "Debt recorded", "id": d.id})


@debts_bp.route("/api/<int:did>/payment", methods=["POST"])
@login_required
@permission_required("manage_debts")
def api_payment(did):
    data = request.get_json() or {}
    amt = to_decimal(data.get("amount"))
    if amt is None or amt <= 0:
        return jsonify({"error": "Invalid amount"}), 400
    try:
        pdate = datetime.fromisoformat(data.get("payment_date")).date() if data.get("payment_date") else date.today()
    except Exception:
        pdate = date.today()
    try:
        DebtService.record_payment(did, amt, pdate, method=data.get("method", "cash"), notes=data.get("notes"), user_id=current_user.id)
    except ValueError as e:
        return jsonify({"error": str(e)}), 400
    return jsonify({"message": "Payment recorded"})


@debts_bp.route("/api/<int:did>/payments")
@login_required
def api_payments(did):
    d = db.session.get(Debt, did)
    if not d:
        return jsonify({"error": "Not found"}), 404
    return jsonify([{
        "id": p.id,
        "amount": float(p.amount),
        "payment_date": p.payment_date.isoformat(),
        "method": p.method,
        "notes": p.notes,
    } for p in d.payments])
