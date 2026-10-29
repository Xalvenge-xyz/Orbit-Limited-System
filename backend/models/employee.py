from datetime import datetime, timezone
from backend.extensions import db


class Employee(db.Model):
    __tablename__ = "employees"
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey("users.id"), nullable=True)
    full_name = db.Column(db.String(120), nullable=False)
    position = db.Column(db.String(80))
    department = db.Column(db.String(80))
    hire_date = db.Column(db.Date)
    salary = db.Column(db.Numeric(12, 2), default=0)
    status = db.Column(db.String(20), default="active")
    notes = db.Column(db.Text)
    created_at = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc))

    user = db.relationship("User", lazy="joined")
