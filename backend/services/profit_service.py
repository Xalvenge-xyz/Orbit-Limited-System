from decimal import Decimal
from backend.extensions import db
from backend.models.sale import Sale
from backend.models.expense import Expense
from backend.models.capital import CapitalTransaction
from backend.models.debt import Debt


class ProfitService:
    @staticmethod
    def period_totals(start_date=None, end_date=None):
        q = Sale.query.filter(Sale.status == "completed")
        if start_date:
            q = q.filter(Sale.created_at >= start_date)
        if end_date:
            q = q.filter(Sale.created_at <= end_date)
        sales = q.all()
        gross_sales = sum((s.total for s in sales), Decimal(0))
        cogs = sum((s.cost_total for s in sales), Decimal(0))
        gross_profit = sum((s.gross_profit for s in sales), Decimal(0))

        # expenses in period
        eq = Expense.query.filter(Expense.status == "recorded")
        if start_date:
            eq = eq.filter(Expense.expense_date >= start_date.date() if hasattr(start_date, "date") else Expense.expense_date >= start_date)
        if end_date:
            eq = eq.filter(Expense.expense_date <= end_date.date() if hasattr(end_date, "date") else Expense.expense_date <= end_date)
        expenses = eq.all()
        operating_expenses = sum((e.amount for e in expenses), Decimal(0))

        net_profit = gross_profit - operating_expenses

        # capital
        capital_contrib = Decimal(0)
        withdrawals = Decimal(0)
        for c in CapitalTransaction.query.all():
            if c.transaction_type == "contribution":
                capital_contrib += c.amount
            elif c.transaction_type == "withdrawal":
                withdrawals += c.amount

        # receivables/payables
        receivables = sum((d.balance for d in Debt.query.filter_by(debt_type="receivable").all() if d.status != "paid"), Decimal(0))
        payables = sum((d.balance for d in Debt.query.filter_by(debt_type="payable").all() if d.status != "paid"), Decimal(0))

        return {
            "gross_sales": gross_sales,
            "cogs": cogs,
            "gross_profit": gross_profit,
            "operating_expenses": operating_expenses,
            "net_profit": net_profit,
            "capital_contributions": capital_contrib,
            "withdrawals": withdrawals,
            "receivables": receivables,
            "payables": payables,
            "sale_count": len(sales),
        }
