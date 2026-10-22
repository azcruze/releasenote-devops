"""Data-access layer. Every query is parameterised."""
import math
import re
import sqlite3
import calendar
from datetime import date, timedelta

from .db import get_db, utc_now

STATUSES = ["Draft", "Scheduled", "Released", "Rolled Back", "Deprecated"]
CATEGORIES = ["Major", "Minor", "Patch", "Hotfix", "Security"]
FIELDS = ("version", "title", "description", "release_date", "status", "category", "features",
          "bug_fixes", "improvements", "deployment_notes", "author")


class DuplicateVersion(Exception):
    pass


def db_ping() -> bool:
    try:
        return get_db().execute("SELECT 1").fetchone()[0] == 1
    except sqlite3.Error:
        return False


def _like(text: str) -> str:
    return "%" + text.replace("\\", "\\\\").replace("%", "\\%").replace("_", "\\_") + "%"


def list_releases(q="", status="", category="", sort="newest", page=1, per_page=8):
    where, params = [], []
    q = q.strip()
    if q:
        term = re.sub(r"^[vV](?=\d)", "", q)
        where.append("(version LIKE ? ESCAPE '\\' OR title LIKE ? ESCAPE '\\')")
        params += [_like(term), _like(q)]
    if status in STATUSES:
        where.append("status = ?")
        params.append(status)
    if category in CATEGORIES:
        where.append("category = ?")
        params.append(category)
    clause = ("WHERE " + " AND ".join(where)) if where else ""
    order = "ASC" if sort == "oldest" else "DESC"
    db = get_db()
    total = db.execute(f"SELECT COUNT(*) FROM releases {clause}", params).fetchone()[0]
    pages = max(1, math.ceil(total / per_page))
    page = min(max(page, 1), pages)
    rows = db.execute(
        f"SELECT * FROM releases {clause} ORDER BY release_date {order}, id {order} LIMIT ? OFFSET ?",
        params + [per_page, (page - 1) * per_page]).fetchall()
    return rows, total, page, pages


def get_release(release_id: int):
    return get_db().execute("SELECT * FROM releases WHERE id = ?", (release_id,)).fetchone()


def version_exists(version: str, exclude_id=None) -> bool:
    row = get_db().execute("SELECT id FROM releases WHERE version = ?", (version,)).fetchone()
    return bool(row) and row["id"] != exclude_id


def create_release(data: dict) -> int:
    now = utc_now()
    db = get_db()
    try:
        cur = db.execute(
            f"INSERT INTO releases ({','.join(FIELDS)},created_at,updated_at) "
            f"VALUES ({','.join('?' * len(FIELDS))},?,?)",
            [data[f] for f in FIELDS] + [now, now])
        db.commit()
    except sqlite3.IntegrityError as exc:
        db.rollback()
        raise DuplicateVersion(data["version"]) from exc
    return cur.lastrowid


def update_release(release_id: int, data: dict) -> bool:
    db = get_db()
    assignments = ",".join(f"{f}=?" for f in FIELDS)
    try:
        cur = db.execute(f"UPDATE releases SET {assignments}, updated_at=? WHERE id=?",
                         [data[f] for f in FIELDS] + [utc_now(), release_id])
        db.commit()
    except sqlite3.IntegrityError as exc:
        db.rollback()
        raise DuplicateVersion(data["version"]) from exc
    return cur.rowcount == 1


def delete_release(release_id: int) -> bool:
    db = get_db()
    cur = db.execute("DELETE FROM releases WHERE id = ?", (release_id,))
    db.commit()
    return cur.rowcount == 1


def neighbours(rel):
    """(older, newer) releases around `rel` in date order."""
    db = get_db()
    d, i = rel["release_date"], rel["id"]
    older = db.execute("SELECT id,version,title FROM releases WHERE release_date < ? OR "
                       "(release_date = ? AND id < ?) ORDER BY release_date DESC, id DESC LIMIT 1",
                       (d, d, i)).fetchone()
    newer = db.execute("SELECT id,version,title FROM releases WHERE release_date > ? OR "
                       "(release_date = ? AND id > ?) ORDER BY release_date ASC, id ASC LIMIT 1",
                       (d, d, i)).fetchone()
    return older, newer


def dashboard_stats(recent=5):
    db = get_db()
    total = db.execute("SELECT COUNT(*) FROM releases").fetchone()[0]
    latest = db.execute("SELECT * FROM releases WHERE status='Released' "
                        "ORDER BY release_date DESC, id DESC LIMIT 1").fetchone()
    counts = {s: 0 for s in STATUSES}
    for row in db.execute("SELECT status, COUNT(*) AS n FROM releases GROUP BY status"):
        counts[row["status"]] = row["n"]
    recent_rows = db.execute("SELECT * FROM releases ORDER BY release_date DESC, id DESC LIMIT ?",
                             (recent,)).fetchall()
    return {"total": total, "latest": latest, "counts": counts, "recent": recent_rows}


def release_date_bounds():
    row = get_db().execute(
        "SELECT MIN(release_date) AS first_date, MAX(release_date) AS last_date FROM releases"
    ).fetchone()
    return row["first_date"], row["last_date"]


def dashboard_analytics(start_date: date, end_date: date, q="", status="", category="",
                        month=None):
    """Return release analytics and calendar data from the live SQLite records."""
    db = get_db()
    base_where, base_params = [], []
    if q.strip():
        term = re.sub(r"^[vV](?=\d)", "", q.strip())
        base_where.append("(version LIKE ? ESCAPE '\\' OR title LIKE ? ESCAPE '\\')")
        base_params.extend([_like(term), _like(q.strip())])
    if category in CATEGORIES:
        base_where.append("category = ?")
        base_params.append(category)
    schedule_where = list(base_where)
    schedule_params = list(base_params)
    base_where.extend(["release_date >= ?", "release_date <= ?"])
    base_params.extend([start_date.isoformat(), end_date.isoformat()])

    status_counts = {value: 0 for value in STATUSES}
    base_clause = "WHERE " + " AND ".join(base_where)
    for row in db.execute(
        f"SELECT status, COUNT(*) AS count FROM releases {base_clause} GROUP BY status",
        base_params,
    ):
        status_counts[row["status"]] = row["count"]

    filtered_where = list(base_where)
    filtered_params = list(base_params)
    if status in STATUSES:
        filtered_where.append("status = ?")
        filtered_params.append(status)
    filtered_clause = "WHERE " + " AND ".join(filtered_where)
    total = db.execute(
        f"SELECT COUNT(*) FROM releases {filtered_clause}", filtered_params
    ).fetchone()[0]
    category_counts = {name: 0 for name in ("Major", "Minor", "Patch")}
    for row in db.execute(
        f"SELECT category, COUNT(*) AS count FROM releases {filtered_clause} "
        "AND category IN ('Major', 'Minor', 'Patch') GROUP BY category",
        filtered_params,
    ):
        category_counts[row["category"]] = row["count"]
    filtered_status_counts = {value: 0 for value in STATUSES}
    for row in db.execute(
        f"SELECT status, COUNT(*) AS count FROM releases {filtered_clause} GROUP BY status",
        filtered_params,
    ):
        filtered_status_counts[row["status"]] = row["count"]

    first_month = start_date.replace(day=1)
    last_month = end_date.replace(day=1)
    months = []
    current_month = first_month
    while current_month <= last_month:
        next_month = (current_month.replace(day=28) + timedelta(days=4)).replace(day=1)
        months.append(current_month.strftime("%Y-%m"))
        current_month = next_month
    monthly_rows = db.execute(
        f"SELECT substr(release_date, 1, 7) AS month, COUNT(*) AS count FROM releases "
        f"{filtered_clause} GROUP BY month",
        filtered_params,
    ).fetchall()
    monthly_counts = {row["month"]: row["count"] for row in monthly_rows}

    latest = db.execute(
        f"SELECT id, version, release_date FROM releases {filtered_clause} "
        "AND status = 'Released' ORDER BY release_date DESC, id DESC LIMIT 1",
        filtered_params,
    ).fetchone()
    recent = db.execute(
        f"SELECT id, version, title, release_date, status, category FROM releases "
        f"{filtered_clause} ORDER BY release_date DESC, id DESC LIMIT 5",
        filtered_params,
    ).fetchall()

    today = date.today().isoformat()
    upcoming_clause = " AND ".join(schedule_where + ["status = ?", "release_date >= ?"])
    upcoming = db.execute(
        f"SELECT id, version, title, release_date, status FROM releases "
        f"WHERE {upcoming_clause} "
        "ORDER BY release_date ASC, id ASC LIMIT 6",
        schedule_params + ["Scheduled", today],
    ).fetchall()

    calendar_month = month or date.today().replace(day=1)
    calendar_start = calendar_month.replace(day=1)
    calendar_end = calendar_month.replace(day=calendar.monthrange(
        calendar_month.year, calendar_month.month)[1])
    calendar_where = list(schedule_where)
    calendar_params = list(schedule_params)
    calendar_where.extend(["release_date >= ?", "release_date <= ?", "status = 'Scheduled'"])
    calendar_params.extend([calendar_start.isoformat(), calendar_end.isoformat()])
    calendar_clause = "WHERE " + " AND ".join(calendar_where)
    scheduled = db.execute(
        f"SELECT id, version, title, release_date FROM releases {calendar_clause} "
        "ORDER BY release_date ASC, id ASC",
        calendar_params,
    ).fetchall()

    return {
        "total": total,
        "status_counts": status_counts,
        "filtered_status_counts": filtered_status_counts,
        "category_counts": category_counts,
        "months": months,
        "monthly_counts": [monthly_counts.get(value, 0) for value in months],
        "latest": dict(latest) if latest else None,
        "recent": [dict(row) for row in recent],
        "upcoming": [dict(row) for row in upcoming],
        "calendar": {
            "year": calendar_month.year,
            "month": calendar_month.month,
            "month_name": calendar_month.strftime("%B %Y"),
            "days_in_month": calendar.monthrange(calendar_month.year, calendar_month.month)[1],
            "first_weekday": calendar_start.weekday(),
            "scheduled": [dict(row) for row in scheduled],
        },
        "start_date": start_date.isoformat(),
        "end_date": end_date.isoformat(),
    }
