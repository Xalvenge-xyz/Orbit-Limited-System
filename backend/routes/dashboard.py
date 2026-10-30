from flask import Blueprint, render_template, jsonify, request, redirect
from flask_login import login_required, current_user
from backend.utils.permissions import permission_required
from backend.services.profit_service import ProfitService
from backend.services.finance_service import FinanceService
from backend.services.notification_service import NotificationService
from backend.models.product import Product, Category
from backend.models.sale import Sale
from datetime import datetime, timedelta, date, timezone
from decimal import Decimal
from collections import defaultdict

dashboard_bp = Blueprint("dashboard", __name__, url_prefix="/dashboard")


@dashboard_bp.route("/")
@login_required
def index():
    if not current_user.has_permission("view_dashboard"):
        return redirect("/pos")
    return render_template("dashboard/index.html")


@dashboard_bp.route("/api/metrics")
@login_required
def api_metrics():
    if not current_user.has_permission("view_dashboard"):
        return jsonify({"error": "Permission denied"}), 403
    period = request.args.get("period", "monthly")
    # Use naive UTC datetimes to match stored DB values
    end_dt = datetime.now(timezone.utc).replace(tzinfo=None)
    start_dt = end_dt - timedelta(days=30)
    totals = ProfitService.period_totals(start_dt, end_dt)
    inv_val = FinanceService.inventory_value()
    cash = FinanceService.cash_balance()
    low_stock = NotificationService.low_stock_products()

    # items sold + sales by date
    sales = Sale.query.filter(Sale.status == "completed", Sale.created_at >= start_dt, Sale.created_at <= end_dt).all()
    items_sold = sum(sum((si.quantity for si in s.items), 0) for s in sales)
    sales_by_date = defaultdict(lambda: Decimal("0"))
    for s in sales:
        d = s.created_at.date().isoformat() if s.created_at else None
        if d:
            sales_by_date[d] += s.total

    # last 14 days
    last_days = []
    for i in range(13, -1, -1):
        day = (end_dt.date() - timedelta(days=i)).isoformat()
        last_days.append({"date": day, "revenue": float(sales_by_date.get(day, Decimal("0")))})

    # inventory by category
    inv_by_cat = defaultdict(lambda: 0)
    for p in Product.query.filter_by(status="active").all():
        cat = p.category.name if p.category else "Uncategorized"
        inv_by_cat[cat] += p.stock
    inv_by_category = [{"category": k, "stock": v} for k, v in inv_by_cat.items()]

    # inventory estimation
    est_capital = Decimal("0")
    est_gross_max = Decimal("0")
    est_gross_min = Decimal("0")
    est_net_max = Decimal("0")
    est_net_min = Decimal("0")
    for p in Product.query.filter_by(status="active").all():
        est_capital += Decimal(str(p.stock)) * Decimal(str(p.cost))
        est_gross_max += Decimal(str(p.stock)) * Decimal(str(p.price))
        est_gross_min += Decimal(str(p.stock)) * Decimal(str(p.min_price))
        est_net_max += Decimal(str(p.stock)) * (Decimal(str(p.price)) - Decimal(str(p.cost)))
        est_net_min += Decimal(str(p.stock)) * (Decimal(str(p.min_price)) - Decimal(str(p.cost)))
    capital = totals["capital_contributions"] - totals["withdrawals"]
    roi = 0.0
    if capital and capital != 0:
        roi = float((totals["net_profit"] / capital) * 100)
    total_stock = sum((p.stock for p in Product.query.filter_by(status="active").all()), 0)
    unpaid_debt = totals["payables"] + totals["receivables"]

    return jsonify({
        "today_sales": float(sum((s.total for s in Sale.query.filter(Sale.created_at >= datetime.combine(datetime.now(timezone.utc).date(), datetime.min.time())).all() if s.status == "completed"), Decimal(0))),
        "gross_sales": float(totals["gross_sales"]),
        "gross_profit": float(totals["gross_profit"]),
        "net_profit": float(totals["net_profit"]),
        "operating_expenses": float(totals["operating_expenses"]),
        "inventory_value": float(inv_val),
        "cash": float(cash),
        "receivables": float(totals["receivables"]),
        "payables": float(totals["payables"]),
        "capital": float(capital),
        "low_stock_count": len(low_stock),
        "sale_count": totals["sale_count"],
        "items_sold": items_sold,
        "roi": roi,
        "total_stock": total_stock,
        "unpaid_debt": float(unpaid_debt),
        "sales_by_date": last_days,
        "inventory_by_category": inv_by_category,
        "est_capital": float(est_capital),
        "est_gross_max": float(est_gross_max),
        "est_gross_min": float(est_gross_min),
        "est_net_max": float(est_net_max),
        "est_net_min": float(est_net_min),
    })
