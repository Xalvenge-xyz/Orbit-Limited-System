from decimal import Decimal
from backend.extensions import db
from backend.models.product import Product
from backend.models.sale import Sale, Payment
from backend.models.expense import Expense
from backend.models.capital import CapitalTransaction
from backend.models.debt import Debt
from backend.models.purchase import Purchase


class FinanceService:
    @staticmethod
    def inventory_value():
        total = Decimal(0)
        for p in Product.query.filter_by(status="active").all():
            total += Decimal(str(p.stock)) * Decimal(str(p.cost))
        return total

    @staticmethod
    def estimated_inventory_profit():
        total = Decimal(0)
        for p in Product.query.filter_by(status="active").all():
            total += Decimal(str(p.stock)) * (Decimal(str(p.price)) - Decimal(str(p.cost)))
        return total

    @staticmethod
    def cash_balance():
        # cash in from sales + debt payments received + capital contributions - expenses paid cash - capital withdrawals - debt payments paid
        cash = Decimal(0)
        for s in Sale.query.filter_by(status="completed").all():
            if s.payment_method == "cash":
                cash += s.total
            else:
                # non-cash payments also count as received funds? treat all completed sale totals as received except receivables tracked separately
                # We'll count non-cash as received too
                pass
        # Count all completed sales totals as cash received (simplified: card/gcash treated as received)
        for s in Sale.query.filter_by(status="completed").all():
            if s.payment_method != "cash":
                cash += s.total
        # debt payments received (customer)
        for d in Debt.query.filter_by(debt_type="receivable").all():
            for p in d.payments:
                cash += p.amount
        # capital contributions
        for c in CapitalTransaction.query.filter_by(transaction_type="contribution").all():
            cash += c.amount
        # purchases paid in cash
        for pu in Purchase.query.all():
            cash -= pu.amount_paid
        # expenses paid in cash
        for e in Expense.query.filter_by(status="recorded").all():
            if e.payment_method == "cash":
                cash -= e.amount
        # capital withdrawals
        for c in CapitalTransaction.query.filter_by(transaction_type="withdrawal").all():
            cash -= c.amount
        # supplier debt payments (payables) - cash out
        for d in Debt.query.filter_by(debt_type="payable").all():
            for p in d.payments:
                cash -= p.amount
        return cash

    @staticmethod
    def safe_spend(eligible_profit, percent):
        percent = max(10, min(80, int(percent)))
        limit = (eligible_profit * Decimal(percent) / Decimal(100)).quantize(Decimal("0.01"))
        buffer = (eligible_profit - limit).quantize(Decimal("0.01"))
        return limit, buffer
