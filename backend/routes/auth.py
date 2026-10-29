from datetime import datetime, timezone, timedelta
import secrets
from flask import Blueprint, render_template, request, redirect, url_for, flash, session
from flask_login import login_user, logout_user, login_required, current_user
from backend.extensions import db
from backend.models.user import User, Role
from backend.utils.validators import validate_email
from backend.utils.audit import log_action
from backend.utils.decorators import rate_limit

auth_bp = Blueprint("auth", __name__, url_prefix="/auth")


def _ensure_roles():
    from backend.models.user import ROLE_PERMISSIONS
    for name, perms in ROLE_PERMISSIONS.items():
        r = Role.query.filter_by(name=name).first()
        if not r:
            r = Role(name=name, description=name.title(), permissions=",".join(perms))
            db.session.add(r)
    db.session.commit()


@auth_bp.route("/setup-owner", methods=["GET", "POST"])
def setup_owner():
    _ensure_roles()
    if User.query.count() > 0:
        flash("Setup already completed.", "info")
        return redirect(url_for("auth.login"))
    if request.method == "POST":
        full_name = request.form.get("full_name", "").strip()
        email = request.form.get("email", "").strip().lower()
        mobile = request.form.get("mobile", "").strip()
        password = request.form.get("password", "")
        confirm = request.form.get("confirm", "")
        if not full_name or not validate_email(email):
            flash("Valid name and email required.", "danger")
            return render_template("auth/setup_owner.html")
        if password != confirm or len(password) < 8:
            flash("Passwords must match and be at least 8 characters.", "danger")
            return render_template("auth/setup_owner.html")
        owner_role = Role.query.filter_by(name="owner").first()
        u = User(full_name=full_name, email=email, mobile=mobile, role_id=owner_role.id, status="approved")
        u.set_password(password)
        u.approved_at = datetime.now(timezone.utc)
        db.session.add(u)
        db.session.commit()
        log_action(u.id, "owner_setup", "user", u.id, "Initial owner created")
        flash("Owner account created. Please log in.", "success")
        return redirect(url_for("auth.login"))
    return render_template("auth/setup_owner.html")


@auth_bp.route("/login", methods=["GET", "POST"])
@rate_limit(lambda: request.remote_addr or "ip", limit=10, window=60)
def login():
    _ensure_roles()
    if current_user.is_authenticated:
        return redirect(url_for("dashboard.index"))
    if request.method == "POST":
        email = request.form.get("email", "").strip().lower()
        password = request.form.get("password", "")
        user = User.query.filter_by(email=email).first()
        if user and user.check_password(password):
            if user.status != "approved":
                flash("Account pending approval or suspended.", "warning")
                return render_template("auth/login.html")
            login_user(user, remember=True)
            flash("Welcome back.", "success")
            nxt = request.args.get("next")
            return redirect(nxt or url_for("dashboard.index"))
        flash("Invalid credentials.", "danger")
    return render_template("auth/login.html")


@auth_bp.route("/register", methods=["GET", "POST"])
def register():
    _ensure_roles()
    if request.method == "POST":
        full_name = request.form.get("full_name", "").strip()
        email = request.form.get("email", "").strip().lower()
        mobile = request.form.get("mobile", "").strip()
        password = request.form.get("password", "")
        confirm = request.form.get("confirm", "")
        if not full_name or not validate_email(email):
            flash("Valid name and email required.", "danger")
            return render_template("auth/register.html")
        if password != confirm or len(password) < 8:
            flash("Passwords must match and be at least 8 characters.", "danger")
            return render_template("auth/register.html")
        if User.query.filter_by(email=email).first():
            flash("Email already registered.", "danger")
            return render_template("auth/register.html")
        cashier_role = Role.query.filter_by(name="cashier").first()
        u = User(full_name=full_name, email=email, mobile=mobile, role_id=cashier_role.id, status="pending")
        u.set_password(password)
        db.session.add(u)
        db.session.commit()
        flash("Registration submitted. Await approval.", "info")
        return redirect(url_for("auth.login"))
    return render_template("auth/register.html")


@auth_bp.route("/logout")
@login_required
def logout():
    logout_user()
    flash("Logged out.", "info")
    return redirect(url_for("auth.login"))


import random
import string


@auth_bp.route("/forgot", methods=["GET", "POST"])
def forgot_password():
    if request.method == "POST":
        email = request.form.get("email", "").strip().lower()
        user = User.query.filter_by(email=email).first()
        if user:
            otp = "".join(random.choices(string.digits, k=6))
            session["otp_code"] = otp
            session["otp_email"] = email
            session["otp_expires"] = (datetime.now(timezone.utc) + timedelta(minutes=10)).isoformat()
            # send email
            try:
                from backend.extensions import mail
                from flask_mail import Message
                msg = Message(
                    subject="ORBIT-POS Password Reset OTP",
                    sender=app_config_mail_sender(),
                    recipients=[email],
                )
                msg.body = f"Your ORBIT-POS password reset code is: {otp}\n\nThis code expires in 10 minutes. If you did not request this, ignore this email."
                mail.send(msg)
                flash("A 6-digit OTP has been sent to your email.", "success")
                print(f"[ORBIT-POS] OTP sent to {email}: {otp}", flush=True)
            except Exception as e:
                # dev fallback: show OTP in flash (remove in production)
                flash(f"Email not configured. Dev OTP: {otp}", "warning")
        else:
            flash("If the account exists, a reset code has been sent.", "info")
        return redirect(url_for("auth.reset_password"))
    return render_template("auth/forgot_password.html")


def app_config_mail_sender():
    from flask import current_app
    return current_app.config.get("MAIL_DEFAULT_SENDER") or "noreply@orbitpos.local"


@auth_bp.route("/reset", methods=["GET", "POST"])
def reset_password():
    if request.method == "POST":
        email = request.form.get("email", "").strip().lower()
        otp = request.form.get("otp", "").strip()
        password = request.form.get("password", "")
        confirm = request.form.get("confirm", "")
        # verify OTP
        stored_code = session.get("otp_code")
        stored_email = session.get("otp_email")
        expires = session.get("otp_expires")
        if not stored_code or not stored_email:
            flash("No pending reset request. Please request a new code.", "danger")
            return redirect(url_for("auth.forgot_password"))
        if expires and datetime.fromisoformat(expires) < datetime.now(timezone.utc):
            flash("OTP expired. Please request a new code.", "danger")
            session.pop("otp_code", None)
            session.pop("otp_email", None)
            session.pop("otp_expires", None)
            return redirect(url_for("auth.forgot_password"))
        if email != stored_email or otp != stored_code:
            flash("Invalid email or OTP code.", "danger")
            return render_template("auth/reset_password.html")
        if password != confirm or len(password) < 8:
            flash("Passwords must match and be at least 8 characters.", "danger")
            return render_template("auth/reset_password.html")
        user = User.query.filter_by(email=email).first()
        if user:
            user.set_password(password)
            db.session.commit()
            session.pop("otp_code", None)
            session.pop("otp_email", None)
            session.pop("otp_expires", None)
            flash("Password updated. Please log in.", "success")
            return redirect(url_for("auth.login"))
        flash("Account not found.", "danger")
    return render_template("auth/reset_password.html")
