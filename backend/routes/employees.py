from flask import Blueprint, render_template, request, jsonify
from flask_login import login_required, current_user
from backend.extensions import db
from backend.models.user import User, Role
from backend.models.employee import Employee
from backend.utils.permissions import permission_required
from backend.utils.audit import log_action

employees_bp = Blueprint("employees", __name__, url_prefix="/employees")


@employees_bp.route("/")
@login_required
@permission_required("manage_employees")
def index():
    return render_template("employees/index.html")


@employees_bp.route("/api/list")
@login_required
@permission_required("manage_employees")
def api_list():
    users = User.query.order_by(User.created_at.desc()).all()
    return jsonify([{
        "id": u.id,
        "full_name": u.full_name,
        "email": u.email,
        "mobile": u.mobile,
        "role": u.role.name if u.role else None,
        "role_id": u.role_id,
        "status": u.status,
        "created_at": u.created_at.isoformat(),
    } for u in users])


@employees_bp.route("/api/roles")
@login_required
@permission_required("manage_employees")
def api_roles():
    roles = Role.query.order_by(Role.name).all()
    return jsonify([{"id": r.id, "name": r.name} for r in roles])


@employees_bp.route("/api/<int:uid>/approve", methods=["POST"])
@login_required
@permission_required("manage_employees")
def api_approve(uid):
    u = db.session.get(User, uid)
    if not u:
        return jsonify({"error": "Not found"}), 404
    u.status = "approved"
    u.approved_by = current_user.id
    from datetime import datetime, timezone
    u.approved_at = datetime.now(timezone.utc)
    db.session.commit()
    log_action(current_user.id, "account_approved", "user", u.id, u.email)
    return jsonify({"message": "Account approved"})


@employees_bp.route("/api/<int:uid>/suspend", methods=["POST"])
@login_required
@permission_required("manage_employees")
def api_suspend(uid):
    u = db.session.get(User, uid)
    if not u:
        return jsonify({"error": "Not found"}), 404
    if u.id == current_user.id:
        return jsonify({"error": "Cannot suspend yourself"}), 400
    u.status = "suspended"
    db.session.commit()
    log_action(current_user.id, "account_suspended", "user", u.id, u.email)
    return jsonify({"message": "Account suspended"})


@employees_bp.route("/api/<int:uid>/role", methods=["POST"])
@login_required
@permission_required("manage_roles")
def api_role(uid):
    u = db.session.get(User, uid)
    if not u:
        return jsonify({"error": "Not found"}), 404
    data = request.get_json() or {}
    role_id = data.get("role_id")
    role = db.session.get(Role, role_id)
    if not role:
        return jsonify({"error": "Invalid role"}), 400
    # prevent granting owner unless current is owner
    if role.name == "owner" and current_user.role_name() != "owner":
        return jsonify({"error": "Cannot assign owner role"}), 403
    u.role_id = role.id
    db.session.commit()
    log_action(current_user.id, "role_changed", "user", u.id, role.name)
    return jsonify({"message": "Role updated"})
