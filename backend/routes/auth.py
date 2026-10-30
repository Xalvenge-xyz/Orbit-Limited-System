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
                from flask import current_app
                otp_sent = False
                # Try SendGrid HTTP API first (free 100/day, sends to ANY email with single sender verification)
                sendgrid_key = current_app.config.get("SENDGRID_API_KEY") or os.environ.get("SENDGRID_API_KEY")
                print(f"[ORBIT-POS] SendGrid key present: {bool(sendgrid_key)}", flush=True)
                if sendgrid_key:
                    try:
                        import json as _json
                        import urllib.request as _urllib
                        import urllib.error as _urlerr
                        sender = current_app.config.get("MAIL_DEFAULT_SENDER") or "noreply@orbitpos.local"
                        payload = _json.dumps({
                            "personalizations": [{"to": [{"email": email}]}],
                            "from": {"email": sender},
                            "subject": "ORBIT-POS Password Reset OTP",
                            "content": [{"type": "text/plain", "value": f"Your ORBIT-POS password reset code is: {otp}\n\nThis code expires in 10 minutes. If you did not request this, ignore this email."}],
                        }).encode()
                        req = _urllib.Request(
                            "https://api.sendgrid.com/v3/mail/send",
                            data=payload,
                            headers={"Authorization": f"Bearer {sendgrid_key}", "Content-Type": "application/json"},
                        )
                        with _urllib.urlopen(req, timeout=10) as resp:
                            body = resp.read().decode()
                            print(f"[ORBIT-POS] SendGrid response: {resp.status} {body}", flush=True)
                            if resp.status in (200, 201, 202):
                                otp_sent = True
                    except _urlerr.HTTPError as he:
                        err_body = he.read().decode() if he.fp else ""
                        print(f"[ORBIT-POS] SendGrid HTTP error: {he.code} {err_body}", flush=True)
                    except Exception as he:
                        print(f"[ORBIT-POS] SendGrid request failed: {he}", flush=True)
                # Fallback: Resend (free, but only sends to account owner email without domain)
                elif current_app.config.get("RESEND_API_KEY") or os.environ.get("RESEND_API_KEY"):
                    resend_key = current_app.config.get("RESEND_API_KEY") or os.environ.get("RESEND_API_KEY")
                    try:
                        import resend as _resend
                        _resend.api_key = resend_key
                        params = {
                            "from": "onboarding@resend.dev",
                            "to": [email],
                            "subject": "ORBIT-POS Password Reset OTP",
                            "html": f"<p>Your ORBIT-POS password reset code is: <strong>{otp}</strong></p><p>This code expires in 10 minutes. If you did not request this, ignore this email.</p>",
                        }
                        resp = _resend.Emails.send(params)
                        print(f"[ORBIT-POS] Resend response: {resp}", flush=True)
                        otp_sent = True
                    except Exception as he:
                        print(f"[ORBIT-POS] Resend failed: {he}", flush=True)
                # Fallback: SMTP (only if explicitly enabled)
                elif current_app.config.get("MAIL_ENABLED") and current_app.config.get("MAIL_USERNAME") and current_app.config.get("MAIL_SERVER"):
                    from backend.extensions import mail
                    from flask_mail import Message
                    msg = Message(
                        subject="ORBIT-POS Password Reset OTP",
                        sender=app_config_mail_sender(),
                        recipients=[email],
                    )
                    msg.body = f"Your ORBIT-POS password reset code is: {otp}\n\nThis code expires in 10 minutes. If you did not request this, ignore this email."
                    mail.send(msg)
                    otp_sent = True

                if otp_sent:
                    flash("A 6-digit OTP has been sent to your email.", "success")
                    print(f"[ORBIT-POS] OTP sent to {email}: {otp}", flush=True)
                else:
                    flash(f"Email unavailable. Dev OTP: {otp}", "warning")
                    print(f"[ORBIT-POS] OTP for {email}: {otp}", flush=True)
            except Exception as e:
                # dev fallback: show OTP on screen if email unavailable
                flash(f"Email unavailable. Dev OTP: {otp}", "warning")
                print(f"[ORBIT-POS] Email failed ({e}); OTP for {email}: {otp}", flush=True)
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
