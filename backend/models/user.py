from datetime import datetime, timezone
from flask_login import UserMixin
from werkzeug.security import generate_password_hash, check_password_hash
from backend.extensions import db


class Permission:
    VIEW_DASHBOARD = "view_dashboard"
    MANAGE_PRODUCTS = "manage_products"
    MANAGE_INVENTORY = "manage_inventory"
    POS_ACCESS = "pos_access"
    VIEW_SALES = "view_sales"
    MANAGE_EXPENSES = "manage_expenses"
    VIEW_FINANCE = "view_finance"
    MANAGE_DEBTS = "manage_debts"
    MANAGE_PURCHASES = "manage_purchases"
    MANAGE_CAPITAL = "manage_capital"
    MANAGE_EMPLOYEES = "manage_employees"
    MANAGE_SETTINGS = "manage_settings"
    MANAGE_ROLES = "manage_roles"
    OVERRIDE_PRICE = "override_price"
    REFUND_VOID = "refund_void"
    EXPORT_REPORTS = "export_reports"


ROLE_PERMISSIONS = {
    "owner": [
        Permission.VIEW_DASHBOARD, Permission.MANAGE_PRODUCTS, Permission.MANAGE_INVENTORY,
        Permission.POS_ACCESS, Permission.VIEW_SALES, Permission.MANAGE_EXPENSES,
        Permission.VIEW_FINANCE, Permission.MANAGE_DEBTS, Permission.MANAGE_PURCHASES,
        Permission.MANAGE_CAPITAL, Permission.MANAGE_EMPLOYEES, Permission.MANAGE_SETTINGS,
        Permission.MANAGE_ROLES, Permission.OVERRIDE_PRICE, Permission.REFUND_VOID,
        Permission.EXPORT_REPORTS,
    ],
    "admin": [
        Permission.VIEW_DASHBOARD, Permission.MANAGE_PRODUCTS, Permission.MANAGE_INVENTORY,
        Permission.POS_ACCESS, Permission.VIEW_SALES, Permission.MANAGE_EXPENSES,
        Permission.VIEW_FINANCE, Permission.MANAGE_DEBTS, Permission.MANAGE_PURCHASES,
        Permission.MANAGE_CAPITAL, Permission.MANAGE_EMPLOYEES, Permission.MANAGE_SETTINGS,
        Permission.OVERRIDE_PRICE, Permission.REFUND_VOID, Permission.EXPORT_REPORTS,
    ],
    "manager": [
        Permission.MANAGE_PRODUCTS, Permission.MANAGE_INVENTORY, Permission.POS_ACCESS,
        Permission.VIEW_SALES, Permission.EXPORT_REPORTS,
    ],
    "cashier": [Permission.POS_ACCESS],
}


class Role(db.Model):
    __tablename__ = "roles"
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(50), unique=True, nullable=False)
    description = db.Column(db.String(255))
    permissions = db.Column(db.Text, default="")
    created_at = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc))

    def permission_list(self):
        return [p for p in self.permissions.split(",") if p]

    def has(self, perm):
        return perm in self.permission_list()


class User(UserMixin, db.Model):
    __tablename__ = "users"
    id = db.Column(db.Integer, primary_key=True)
    full_name = db.Column(db.String(120), nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False, index=True)
    mobile = db.Column(db.String(30))
    password_hash = db.Column(db.String(255), nullable=False)
    role_id = db.Column(db.Integer, db.ForeignKey("roles.id"), nullable=False)
    status = db.Column(db.String(20), default="pending", nullable=False)  # pending/approved/suspended
    created_at = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc))
    updated_at = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc), onupdate=lambda: datetime.now(timezone.utc))
    approved_by = db.Column(db.Integer, db.ForeignKey("users.id"), nullable=True)
    approved_at = db.Column(db.DateTime, nullable=True)

    role = db.relationship("Role", foreign_keys=[role_id], lazy="joined")
    approver = db.relationship("User", foreign_keys=[approved_by], remote_side=[id])

    def set_password(self, password):
        self.password_hash = generate_password_hash(password)

    def check_password(self, password):
        return check_password_hash(self.password_hash, password)

    def has_permission(self, perm):
        if self.status != "approved":
            return False
        if self.role is None:
            return False
        if self.role.name == "owner":
            return True
        return self.role.has(perm)

    @property
    def is_active(self):
        return self.status == "approved"

    def get_id(self):
        return str(self.id)

    def role_name(self):
        return self.role.name if self.role else None
