import os
from datetime import timedelta


def _fix_db_url(url):
    # Render provides postgres:// ; SQLAlchemy 1.4+ requires postgresql://
    if url and url.startswith("postgres://"):
        url = url.replace("postgres://", "postgresql://", 1)
    # TiDB/MySQL default URLs use mysql:// ; force PyMySQL driver
    if url and url.startswith("mysql://"):
        url = url.replace("mysql://", "mysql+pymysql://", 1)
    return url


def _engine_options(url):
    opts = {
        "pool_pre_ping": True,
        "pool_recycle": 3600,
    }
    # TiDB Cloud requires TLS; enable it (verify off to avoid bundling CA cert)
    if url and "tidbcloud.com" in url:
        opts["connect_args"] = {"ssl": {"verify_cert": False, "verify_identity": False}}
    return opts


class Config:
    SECRET_KEY = os.environ.get("SECRET_KEY", "dev-secret-change-me")
    SQLALCHEMY_DATABASE_URI = _fix_db_url(os.environ.get(
        "DATABASE_URL", "mysql+pymysql://root:@127.0.0.1:3306/orbit_pos"
    ))
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    SQLALCHEMY_ENGINE_OPTIONS = _engine_options(SQLALCHEMY_DATABASE_URI)

    # Sessions
    PERMANENT_SESSION_LIFETIME = timedelta(hours=8)
    SESSION_COOKIE_HTTPONLY = True
    SESSION_COOKIE_SAMESITE = "Lax"
    SESSION_COOKIE_SECURE = os.environ.get("FLASK_ENV", "").lower() == "production" or os.environ.get("RENDER") == "true"

    # WTF
    WTF_CSRF_ENABLED = True
    WTF_CSRF_TIME_LIMIT = None

    # Mail (optional)
    MAIL_SERVER = os.environ.get("MAIL_SERVER")
    MAIL_PORT = int(os.environ.get("MAIL_PORT", 587))
    MAIL_USE_TLS = os.environ.get("MAIL_USE_TLS", "true").lower() == "true"
    MAIL_USERNAME = os.environ.get("MAIL_USERNAME")
    MAIL_PASSWORD = os.environ.get("MAIL_PASSWORD")
    MAIL_DEFAULT_SENDER = os.environ.get("MAIL_DEFAULT_SENDER", "noreply@orbitpos.local")
    MAIL_TIMEOUT = int(os.environ.get("MAIL_TIMEOUT", 5))
    MAIL_ENABLED = os.environ.get("MAIL_ENABLED", "false").lower() == "true"
    RESEND_API_KEY = os.environ.get("RESEND_API_KEY")

    # OAuth (optional)
    GOOGLE_CLIENT_ID = os.environ.get("GOOGLE_CLIENT_ID")
    GOOGLE_CLIENT_SECRET = os.environ.get("GOOGLE_CLIENT_SECRET")

    # App settings
    LOW_STOCK_THRESHOLD = 3
    CURRENCY_SYMBOL = "₱"
