"""Lightweight management authentication and CSRF protection.

Management modes (decided by configuration):
  protected  - ADMIN_PASSWORD_HASH or ADMIN_PASSWORD is set: sign-in required to change data.
  open       - no password, APP_ENV is development/testing: anyone may change data (local use only).
  read-only  - no password in production: writes are refused. Safe default for a public VM.
"""
import hmac
import secrets
import time
from functools import wraps
from urllib.parse import urlparse

from flask import abort, current_app, redirect, request, session, url_for
from werkzeug.security import check_password_hash

MAX_ATTEMPTS, WINDOW_SECONDS = 5, 300


def management_mode() -> str:
    cfg = current_app.config
    if cfg["ADMIN_PASSWORD_HASH"] or cfg["ADMIN_PASSWORD"]:
        return "protected"
    return "open" if cfg["APP_ENV"] in {"development", "testing"} else "read-only"


def can_manage() -> bool:
    mode = management_mode()
    return mode == "open" or (mode == "protected" and bool(session.get("admin")))


def manage_required(view):
    @wraps(view)
    def wrapper(*args, **kwargs):
        mode = management_mode()
        if mode == "read-only":
            abort(403, description="Management is disabled until an administrator password is "
                                   "configured on the server.")
        if mode == "protected" and not session.get("admin"):
            return redirect(url_for("main.login", next=request.full_path.rstrip("?")))
        return view(*args, **kwargs)
    return wrapper


def csrf_token() -> str:
    if "csrf" not in session:
        session["csrf"] = secrets.token_urlsafe(32)
    return session["csrf"]


def verify_password(candidate: str) -> bool:
    cfg = current_app.config
    if cfg["ADMIN_PASSWORD_HASH"]:
        return check_password_hash(cfg["ADMIN_PASSWORD_HASH"], candidate)
    if cfg["ADMIN_PASSWORD"]:
        return hmac.compare_digest(cfg["ADMIN_PASSWORD"].encode(), candidate.encode())
    return False


def safe_next(target: str) -> str:
    """Only allow same-site relative redirects (prevents open redirects)."""
    parsed = urlparse(target or "")
    if target and target.startswith("/") and not target.startswith("//") and not parsed.netloc:
        return target
    return url_for("main.dashboard")


def throttled() -> bool:
    attempts = current_app.extensions["login_attempts"].get(request.remote_addr, [])
    return len([t for t in attempts if time.time() - t < WINDOW_SECONDS]) >= MAX_ATTEMPTS


def record_failure() -> None:
    store = current_app.extensions["login_attempts"]
    store.setdefault(request.remote_addr, []).append(time.time())


def init_app(app) -> None:
    app.extensions["login_attempts"] = {}   # per-worker, in-memory (documented limitation)

    @app.before_request
    def _csrf_protect():
        if request.method in {"POST", "PUT", "PATCH", "DELETE"}:
            sent = request.form.get("csrf_token", "")
            expected = session.get("csrf", "")
            if not expected or not hmac.compare_digest(sent, expected):
                abort(400, description="Security token missing or expired. Reload the page and try again.")

    @app.context_processor
    def _inject():
        return {"csrf_token": csrf_token, "can_manage": can_manage(), "management_mode": management_mode()}
