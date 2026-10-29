from functools import wraps
from flask import abort, flash, redirect, url_for, request, jsonify
from flask_login import current_user


def login_required_custom(f):
    @wraps(f)
    def decorated(*args, **kwargs):
        if not current_user.is_authenticated:
            if request.is_json or request.path.startswith("/api"):
                return jsonify({"error": "Authentication required"}), 401
            flash("Please log in.", "warning")
            return redirect(url_for("auth.login"))
        return f(*args, **kwargs)
    return decorated


def permission_required(perm):
    def decorator(f):
        @wraps(f)
        def decorated(*args, **kwargs):
            if not current_user.is_authenticated:
                if request.is_json or request.path.startswith("/api"):
                    return jsonify({"error": "Authentication required"}), 401
                flash("Please log in.", "warning")
                return redirect(url_for("auth.login"))
            if not current_user.has_permission(perm):
                if request.is_json or request.path.startswith("/api"):
                    return jsonify({"error": "Permission denied"}), 403
                flash("You do not have permission to perform this action.", "danger")
                return redirect(url_for("dashboard.index"))
            return f(*args, **kwargs)
        return decorated
    return decorator


def owner_required(f):
    return permission_required("manage_settings")(f)


def role_required(*roles):
    def decorator(f):
        @wraps(f)
        def decorated(*args, **kwargs):
            if not current_user.is_authenticated:
                return redirect(url_for("auth.login"))
            if current_user.role_name() not in roles:
                flash("Permission denied.", "danger")
                return redirect(url_for("dashboard.index"))
            return f(*args, **kwargs)
        return decorated
    return decorator
