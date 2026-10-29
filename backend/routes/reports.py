from flask import Blueprint, render_template, request, jsonify
from flask_login import login_required, current_user
from backend.extensions import db
from backend.models.sale import Sale
from backend.models.expense import Expense
from backend.models.inventory import StockMovement
from backend.models.capital import CapitalTransaction
from backend.models.debt import Debt
from backend.utils.permissions import permission_required
from backend.services.reporting_service import ReportingService
from backend.services.profit_service import ProfitService
from backend.services.finance_service import FinanceService

reports_bp = Blueprint("reports", __name__, url_prefix="/reports")


@reports_bp.route("/")
@login_required
def index():
    return render_template("reports/index.html")


@reports_bp.route("/api/sales")
@login_required
def api_sales():
    period = request.args.get("period", "monthly")
    s, e = ReportingService.parse_range(period, request.args.get("start"), request.args.get("end"))
    sales = ReportingService.sales_report(s, e)
    # cashier only own
    if not current_user.has_permission("view_sales"):
        sales = [x for x in sales if x.user_id == current_user.id]
    return jsonify([x.to_dict() for x in sales])


@reports_bp.route("/api/summary")
@login_required
def api_summary():
    period = request.args.get("period", "monthly")
    s, e = ReportingService.parse_range(period, request.args.get("start"), request.args.get("end"))
    totals = ProfitService.period_totals(s, e)
    return jsonify({k: (float(v) if not isinstance(v, int) else v) for k, v in totals.items()})


@reports_bp.route("/api/stock-movements")
@login_required
def api_stock_movements():
    period = request.args.get("period", "monthly")
    s, e = ReportingService.parse_range(period, request.args.get("start"), request.args.get("end"))
    moves = ReportingService.stock_movements(s, e)
    return jsonify([{
        "id": m.id,
        "product_name": m.product.name if m.product else None,
        "quantity_change": m.quantity_change,
        "movement_type": m.movement_type,
        "reason": m.reason,
        "user": m.user.full_name if m.user else None,
        "created_at": m.created_at.isoformat(),
    } for m in moves])
