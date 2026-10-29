from flask import Blueprint, render_template, request, jsonify
from flask_login import login_required, current_user
from backend.extensions import db
from backend.models.capital import CapitalTransaction
from backend.models.debt import Debt
from backend.utils.permissions import permission_required
from backend.utils.validators import to_decimal
from backend.services.finance_service import FinanceService
from backend.services.profit_service import ProfitService
from backend.utils.audit import log_action
from datetime import datetime, date

finance_bp = Blueprint("finance", __name__, url_prefix="/finance")


@finance_bp.route("/")
@login_required
@permission_required("view_finance")
def index():
    return render_template("finance/index.html")


@finance_bp.route("/api/overview")
@login_required
@permission_required("view_finance")
def api_overview():
    period = request.args.get("period", "monthly")
    start, end = None, None
    from backend.services.reporting_service import ReportingService
    s, e = ReportingService.parse_range(period, request.args.get("start"), request.args.get("end"))
    totals = ProfitService.period_totals(s, e)
    inv_val = FinanceService.inventory_value()
    inv_profit = FinanceService.estimated_inventory_profit()
    cash = FinanceService.cash_balance()
    capital = totals["capital_contributions"] - totals["withdrawals"]
    receivables = totals["receivables"]
    payables = totals["payables"]
    safe_limit, buf = FinanceService.safe_spend(totals["net_profit"], int(request.args.get("percent", 30)))
    return jsonify({
        "gross_sales": float(totals["gross_sales"]),
        "cogs": float(totals["cogs"]),
        "gross_profit": float(totals["gross_profit"]),
        "operating_expenses": float(totals["operating_expenses"]),
        "net_profit": float(totals["net_profit"]),
        "inventory_value": float(inv_val),
        "estimated_inventory_profit": float(inv_profit),
        "cash": float(cash),
        "capital": float(capital),
        "receivables": float(receivables),
        "payables": float(payables),
        "safe_spend": float(safe_limit),
        "protected_buffer": float(buf),
        "capital_contributions": float(totals["capital_contributions"]),
        "withdrawals": float(totals["withdrawals"]),
    })


@finance_bp.route("/api/capital", methods=["GET"])
@login_required
@permission_required("manage_capital")
def api_capital_list():
    items = CapitalTransaction.query.order_by(CapitalTransaction.created_at.desc()).all()
    return jsonify([{
        "id": c.id,
        "type": c.transaction_type,
        "amount": float(c.amount),
        "description": c.description,
        "date": c.transaction_date.isoformat(),
        "user": c.user.full_name if c.user else None,
    } for c in items])


@finance_bp.route("/api/capital", methods=["POST"])
@login_required
@permission_required("manage_capital")
def api_capital_create():
    data = request.get_json() or {}
    ttype = data.get("transaction_type")
    if ttype not in ("contribution", "withdrawal", "adjustment"):
        return jsonify({"error": "Invalid type"}), 400
    amt = to_decimal(data.get("amount"))
    if amt is None or amt <= 0:
        return jsonify({"error": "Invalid amount"}), 400
    try:
        tdate = datetime.fromisoformat(data.get("transaction_date")).date() if data.get("transaction_date") else date.today()
    except Exception:
        tdate = date.today()
    c = CapitalTransaction(
        transaction_type=ttype,
        amount=amt,
        description=(data.get("description") or "").strip(),
        transaction_date=tdate,
        user_id=current_user.id,
    )
    db.session.add(c)
    db.session.commit()
    log_action(current_user.id, "capital_" + ttype, "capital", c.id, str(amt))
    return jsonify({"message": "Capital transaction recorded", "id": c.id})
