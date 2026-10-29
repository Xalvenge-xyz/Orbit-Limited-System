from flask import request
from backend.extensions import db
from backend.models.audit_log import AuditLog


def log_action(user_id, action, entity_type=None, entity_id=None, details=None):
    try:
        entry = AuditLog(
            user_id=user_id,
            action=action,
            entity_type=entity_type,
            entity_id=entity_id,
            details=details,
            ip_address=request.remote_addr if request else None,
        )
        db.session.add(entry)
        db.session.commit()
    except Exception:
        db.session.rollback()
