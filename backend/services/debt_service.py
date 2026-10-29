from decimal import Decimal
from backend.extensions import db
from backend.models.debt import Debt, DebtPayment
from backend.utils.audit import log_action


class DebtService:
    @staticmethod
    def create_debt(name, debt_type, amount, debt_date, due_date=None, notes=None,
                    reference_type=None, reference_id=None, supplier_id=None, user_id=None):
        d = Debt(
            name=name,
            debt_type=debt_type,
            amount=Decimal(str(amount)),
            balance=Decimal(str(amount)),
            paid_amount=Decimal(0),
            status="unpaid",
            debt_date=debt_date,
            due_date=due_date,
            notes=notes,
            reference_type=reference_type,
            reference_id=reference_id,
            supplier_id=supplier_id,
            user_id=user_id,
        )
        db.session.add(d)
        db.session.commit()
        return d

    @staticmethod
    def record_payment(debt_id, amount, payment_date, method="cash", notes=None, user_id=None):
        debt = db.session.get(Debt, debt_id)
        if not debt:
            raise ValueError("Debt not found")
        amt = Decimal(str(amount))
        if amt <= 0:
            raise ValueError("Payment amount must be positive")
        if amt > debt.balance and debt.balance > 0:
            raise ValueError("Payment exceeds outstanding balance")
        pay = DebtPayment(
            debt_id=debt.id,
            amount=amt,
            payment_date=payment_date,
            method=method,
            notes=notes,
            user_id=user_id,
        )
        db.session.add(pay)
        db.session.flush()
        debt.payments.append(pay) if pay not in debt.payments else None
        debt.recompute()
        db.session.commit()
        # also record cash payment via Payment? optional
        log_action(user_id, "debt_payment", "debt", debt.id, f"Amount {amt}")
        return pay
