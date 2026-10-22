"""HTTP routes."""
import platform
import sqlite3
from datetime import date, datetime, timedelta, timezone

from importlib.metadata import version as pkg_version
from flask import (Blueprint, abort, current_app, flash, jsonify, redirect,
                   render_template, request, session, url_for)

from . import auth, models
from .validation import validate_release

bp = Blueprint("main", __name__)


def _now_utc() -> str:
    return datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


def _get_or_404(release_id: int):
    rel = models.get_release(release_id)
    if rel is None:
        abort(404, description="That release does not exist. It may have been deleted.")
    return rel


def _dashboard_filters():
    today = date.today()
    def parse_date(value, fallback):
        if not value:
            return fallback
        parsed = date.fromisoformat(value)
        if parsed.isoformat() != value:
            raise ValueError("Use YYYY-MM-DD for date filters.")
        return parsed

    earliest, latest = models.release_date_bounds()
    end_default = max(today, date.fromisoformat(latest)) if latest else today
    end_date = parse_date(request.args.get("end", ""), end_default)
    start_default = date.fromisoformat(earliest) if earliest else end_date.replace(day=1)
    if not earliest:
        for _ in range(11):
            start_default = (start_default - timedelta(days=1)).replace(day=1)
    start_date = parse_date(request.args.get("start", ""), start_default)
    if start_date > end_date:
        raise ValueError("The start date must be on or before the end date.")
    if (end_date - start_date).days > 3660:
        raise ValueError("Choose a date range of 10 years or less.")

    month_text = request.args.get("month", "")
    month = None
    if month_text:
        parsed_month = datetime.strptime(month_text, "%Y-%m").date()
        if parsed_month.strftime("%Y-%m") != month_text:
            raise ValueError("Use YYYY-MM for the calendar month.")
        month = parsed_month.replace(day=1)
    return {
        "start_date": start_date,
        "end_date": end_date,
        "q": request.args.get("q", "")[:100],
        "status": request.args.get("status", ""),
        "category": request.args.get("category", ""),
        "month": month,
    }


def _dashboard_analytics():
    filters = _dashboard_filters()
    return models.dashboard_analytics(**filters), filters


@bp.get("/")
def dashboard():
    try:
        analytics, filters = _dashboard_analytics()
    except (ValueError, OverflowError) as exc:
        abort(400, description=str(exc))
    return render_template("dashboard.html", analytics=analytics, filters=filters)


@bp.get("/api/dashboard")
def dashboard_data():
    try:
        analytics, _filters = _dashboard_analytics()
    except (ValueError, OverflowError) as exc:
        return jsonify({"error": str(exc)}), 400
    response = jsonify(analytics)
    response.headers["Cache-Control"] = "no-store"
    return response


@bp.get("/releases")
def release_list():
    q = request.args.get("q", "")[:100]
    status = request.args.get("status", "")
    category = request.args.get("category", "")
    sort = "oldest" if request.args.get("sort") == "oldest" else "newest"
    page = request.args.get("page", 1, type=int) or 1
    per_page = current_app.config["PER_PAGE"]
    rows, total, page, pages = models.list_releases(q, status, category, sort, page, per_page)
    filters = {"q": q, "status": status, "category": category, "sort": sort}
    return render_template("release_list.html", releases=rows, total=total, page=page, pages=pages,
                           per_page=per_page, filters=filters,
                           filtered=bool(q or status in models.STATUSES or category in models.CATEGORIES))


@bp.route("/releases/new", methods=["GET", "POST"])
@auth.manage_required
def release_create():
    form, errors = {"status": "Draft", "category": "Minor",
                    "release_date": datetime.now(timezone.utc).date().isoformat()}, {}
    if request.method == "POST":
        form, errors = validate_release(request.form)
        if not errors:
            try:
                new_id = models.create_release(form)
            except models.DuplicateVersion:
                errors = {"version": f"Version {form['version']} already exists. Choose a different version."}
            else:
                flash(f"Release v{form['version']} was created.", "success")
                return redirect(url_for("main.release_detail", release_id=new_id))
        flash("The release was not saved. Fix the highlighted fields and try again.", "error")
        return render_template("release_form.html", form=form, errors=errors, mode="create"), 422
    return render_template("release_form.html", form=form, errors=errors, mode="create")


@bp.get("/releases/<int:release_id>")
def release_detail(release_id):
    rel = _get_or_404(release_id)
    older, newer = models.neighbours(rel)
    return render_template("release_detail.html", r=rel, older=older, newer=newer)


@bp.route("/releases/<int:release_id>/edit", methods=["GET", "POST"])
@auth.manage_required
def release_edit(release_id):
    rel = _get_or_404(release_id)
    form, errors = dict(rel), {}
    if request.method == "POST":
        form, errors = validate_release(request.form, existing_id=release_id)
        if not errors:
            try:
                models.update_release(release_id, form)
            except models.DuplicateVersion:
                errors = {"version": f"Version {form['version']} already exists. Choose a different version."}
            else:
                flash(f"Release v{form['version']} was updated.", "success")
                return redirect(url_for("main.release_detail", release_id=release_id))
        flash("Changes were not saved. Fix the highlighted fields and try again.", "error")
        return render_template("release_form.html", form=form, errors=errors, mode="edit", r=rel), 422
    return render_template("release_form.html", form=form, errors=errors, mode="edit", r=rel)


@bp.route("/releases/<int:release_id>/delete", methods=["GET", "POST"])
@auth.manage_required
def release_delete(release_id):
    rel = _get_or_404(release_id)
    if request.method == "POST":
        models.delete_release(release_id)
        flash(f"Release v{rel['version']} was deleted.", "success")
        return redirect(url_for("main.release_list"))
    return render_template("release_delete.html", r=rel)


@bp.get("/about")
def about():
    cfg = current_app.config
    info = {
        "App version": cfg["APP_VERSION"], "Environment": cfg["APP_ENV"],
        "Build (commit)": cfg["BUILD_INFO"]["commit"],
        "Build number": cfg["BUILD_INFO"]["build_number"] or "not a Jenkins build",
        "Built at": cfg["BUILD_INFO"]["built_at"] or "n/a",
        "Python": platform.python_version(), "Flask": pkg_version("flask"),
        "SQLite library": sqlite3.sqlite_version, "Server time (UTC)": _now_utc(),
        "Management mode": auth.management_mode(),
    }
    return render_template("about.html", info=info)


@bp.get("/health")
def health():
    ok = models.db_ping()
    body = {"status": "ok" if ok else "degraded", "database": "ok" if ok else "unavailable",
            "app": current_app.config["APP_NAME"], "version": current_app.config["APP_VERSION"],
            "build": current_app.config["BUILD_INFO"]["commit"], "timestamp": _now_utc()}
    resp = jsonify(body)
    resp.status_code = 200 if ok else 503
    resp.headers["Cache-Control"] = "no-store"
    return resp


@bp.route("/login", methods=["GET", "POST"])
def login():
    mode = auth.management_mode()
    nxt = auth.safe_next(request.values.get("next", ""))
    if mode != "protected":
        return render_template("login.html", next=nxt)
    if request.method == "POST":
        if auth.throttled():
            flash("Too many failed attempts. Wait a few minutes and try again.", "error")
            return render_template("login.html", next=nxt), 429
        if auth.verify_password(request.form.get("password", "")):
            session.clear()
            session["admin"] = True
            session.permanent = True
            flash("You are signed in.", "success")
            return redirect(nxt)
        auth.record_failure()
        flash("Incorrect password.", "error")
        return render_template("login.html", next=nxt), 401
    return render_template("login.html", next=nxt)


@bp.post("/logout")
def logout():
    session.clear()
    flash("You have been signed out.", "success")
    return redirect(url_for("main.dashboard"))
