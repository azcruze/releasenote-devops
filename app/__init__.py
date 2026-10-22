"""ReleaseNote application factory."""
import secrets

from flask import Flask, render_template
from werkzeug.exceptions import HTTPException

from config import BASE_DIR, Config

from . import auth, cli, db
from .buildinfo import read_build_info
from .routes import bp

ERROR_TITLES = {400: "Request could not be completed", 403: "Action not permitted",
                404: "Page not found", 405: "Method not allowed",
                413: "Submission too large", 429: "Too many attempts"}


def create_app(test_config=None):
    app = Flask(__name__)
    app.config.from_object(Config)
    if test_config:
        app.config.update(test_config)

    if not app.config["SECRET_KEY"]:
        if app.config["APP_ENV"] == "production":
            raise RuntimeError("SECRET_KEY must be set when APP_ENV=production")
        app.config["SECRET_KEY"] = secrets.token_hex(32)   # per-process; sessions reset on restart
    app.config["BUILD_INFO"] = read_build_info(BASE_DIR)
    if app.config["BUILD_ID"]:
        app.config["BUILD_INFO"]["commit"] = app.config["BUILD_ID"]

    db.init_app(app)
    auth.init_app(app)
    cli.register(app)
    app.register_blueprint(bp)

    @app.template_filter("lines")
    def lines(value):
        return [ln.strip() for ln in (value or "").splitlines() if ln.strip()]

    @app.template_filter("pretty_date")
    def pretty_date(value):
        from datetime import date
        try:
            d = date.fromisoformat(value)
            return f"{d.day} {d.strftime('%b %Y')}"
        except (TypeError, ValueError):
            return value or ""

    @app.errorhandler(HTTPException)
    def http_error(err):
        return render_template("error.html", code=err.code,
                               title=ERROR_TITLES.get(err.code, err.name),
                               message=err.description), err.code

    @app.errorhandler(Exception)
    def server_error(err):
        app.logger.exception("Unhandled error: %s", err)
        return render_template("error.html", code=500, title="Something went wrong",
                               message="The error has been logged. Try again in a moment."), 500

    @app.after_request
    def security_headers(resp):
        resp.headers.setdefault("X-Content-Type-Options", "nosniff")
        resp.headers.setdefault("X-Frame-Options", "DENY")
        resp.headers.setdefault("Referrer-Policy", "same-origin")
        resp.headers.setdefault("Content-Security-Policy",
            "default-src 'self'; img-src 'self' data:; frame-ancestors 'none'; "
            "base-uri 'self'; form-action 'self'")
        return resp

    with app.app_context():
        db.init_db()
        if app.config.get("AUTO_SEED"):
            db.seed_demo()
    return app
