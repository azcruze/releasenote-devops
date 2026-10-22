import sqlite3

import pytest

from app import create_app
from app.db import seed_demo, reset_demo
from conftest import make_app


def test_app_starts_and_creates_schema(app):
    assert app.config["TESTING"]
    con = sqlite3.connect(app.config["DATABASE_PATH"])
    tables = {r[0] for r in con.execute("SELECT name FROM sqlite_master WHERE type='table'")}
    con.close()
    assert "releases" in tables
    columns = {r[1] for r in sqlite3.connect(app.config["DATABASE_PATH"]).execute(
        "PRAGMA table_info(releases)")}
    assert "description" in columns


def test_dashboard_empty_state(client):
    resp = client.get("/")
    assert resp.status_code == 200
    assert b"No releases yet" in resp.data


def test_dashboard_with_data(client, seeded):
    html = client.get("/").get_data(as_text=True)
    assert "Total releases" in html
    assert "v2.4.3" in html
    assert "Releases by status" in html
    assert "25" in html


def test_health_ok_and_json_shape(client):
    resp = client.get("/health")
    body = resp.get_json()
    assert resp.status_code == 200
    assert body["status"] == "ok" and body["database"] == "ok"
    assert set(body) == {"status", "database", "app", "version", "build", "timestamp"}
    assert resp.headers["Cache-Control"] == "no-store"


def test_health_reports_database_failure_without_leaking(app, monkeypatch):
    from app import models
    monkeypatch.setattr(models, "db_ping", lambda: False)
    resp = app.test_client().get("/health")
    assert resp.status_code == 503
    assert resp.get_json()["status"] == "degraded"
    assert str(app.config["DATABASE_PATH"]) not in resp.get_data(as_text=True)


def test_database_connectivity(app):
    from app import models
    with app.app_context():
        assert models.db_ping() is True


def test_seed_is_idempotent(app):
    with app.app_context():
        first = seed_demo()
        second = seed_demo()
        assert first == 25 and second == 0
        assert reset_demo() == 25


def test_auto_seed_is_idempotent_across_startups(tmp_path):
    a = make_app(tmp_path, AUTO_SEED=True)
    b = create_app(dict(a.config, AUTO_SEED=True))   # second start-up on the same database
    with b.app_context():
        from app.db import get_db
        assert get_db().execute("SELECT COUNT(*) FROM releases").fetchone()[0] == 25


def test_app_factory_seeds_when_auto_seed_is_not_overridden(tmp_path, monkeypatch):
    from config import Config
    monkeypatch.setattr(Config, "AUTO_SEED", True)
    app = create_app({
        "TESTING": True,
        "APP_ENV": "testing",
        "SECRET_KEY": "test-secret",
        "DATABASE_PATH": str(tmp_path / "default-seed.db"),
    })
    with app.app_context():
        from app.db import get_db
        assert get_db().execute("SELECT COUNT(*) FROM releases").fetchone()[0] == 25


def test_fresh_database_is_seeded_with_25_records(tmp_path):
    app = make_app(tmp_path, AUTO_SEED=True)
    with app.app_context():
        from app.db import get_db
        db = get_db()
        assert db.execute("SELECT COUNT(*) FROM releases").fetchone()[0] == 25
        assert tuple(db.execute("SELECT MIN(version), MAX(version) FROM releases").fetchone()) == (
            "1.6.0", "2.5.0")
        assert db.execute("SELECT COUNT(DISTINCT version) FROM releases").fetchone()[0] == 25
        rows = db.execute(
            "SELECT release_date,description,deployment_notes FROM releases ORDER BY release_date"
        ).fetchall()
        assert [row["release_date"] for row in rows] == sorted(row["release_date"] for row in rows)
        assert all(row["description"] for row in rows)


def test_seeded_status_counts_match_dashboard(client, seeded):
    from app import models
    with seeded.app_context():
        stats = models.dashboard_stats()
        assert stats["total"] == 25
        assert stats["counts"] == {
            "Draft": 1, "Scheduled": 2, "Released": 18,
            "Rolled Back": 2, "Deprecated": 2,
        }
    html = client.get("/").get_data(as_text=True)
    assert "2.4.3" in html and "11 Jun 2026" in html
    for status, count in stats["counts"].items():
        assert f'aria-label="{status}: {count} of 25"' in html


def test_existing_user_release_survives_startup_migration(tmp_path):
    path = tmp_path / "existing.db"
    connection = sqlite3.connect(path)
    connection.executescript("""
        CREATE TABLE releases (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            version TEXT NOT NULL UNIQUE, title TEXT NOT NULL,
            release_date TEXT NOT NULL, status TEXT NOT NULL, category TEXT NOT NULL,
            features TEXT NOT NULL DEFAULT '', bug_fixes TEXT NOT NULL DEFAULT '',
            improvements TEXT NOT NULL DEFAULT '', deployment_notes TEXT NOT NULL DEFAULT '',
            author TEXT NOT NULL, created_at TEXT NOT NULL, updated_at TEXT NOT NULL
        );
        INSERT INTO releases (version,title,release_date,status,category,author,created_at,updated_at)
        VALUES ('9.9.9','My release','2026-09-01','Released','Major','User','now','now');
    """)
    connection.close()

    app = make_app(tmp_path, DATABASE_PATH=str(path), AUTO_SEED=True)
    with app.app_context():
        from app.db import get_db
        row = get_db().execute("SELECT version,title,description FROM releases").fetchone()
        assert tuple(row) == ("9.9.9", "My release", "")
        assert get_db().execute("SELECT COUNT(*) FROM releases").fetchone()[0] == 26


def test_seed_skips_existing_version_without_replacing_user_record(app):
    from app.db import get_db
    with app.app_context():
        get_db().execute(
            """INSERT INTO releases
               (version,title,description,release_date,status,category,author,created_at,updated_at)
               VALUES ('1.6.0','User-authored title','User description','2026-09-01',
                       'Released','Major','User','now','now')""")
        get_db().commit()
        assert seed_demo() == 24
        row = get_db().execute(
            "SELECT title,description FROM releases WHERE version='1.6.0'").fetchone()
        assert tuple(row) == ("User-authored title", "User description")
        assert get_db().execute("SELECT COUNT(*) FROM releases").fetchone()[0] == 25


def test_reset_demo_command_is_blocked_outside_development(app):
    result = app.test_cli_runner().invoke(args=["reset-demo", "--yes"])
    assert result.exit_code != 0
    assert "allowed only when APP_ENV=development" in result.output


def test_reset_demo_command_reseeds_isolated_development_database(tmp_path):
    app = make_app(tmp_path, APP_ENV="development", AUTO_SEED=False)
    result = app.test_cli_runner().invoke(args=["reset-demo", "--yes"])
    assert result.exit_code == 0
    assert "25 demo release(s) inserted" in result.output
    with app.app_context():
        from app.db import get_db
        assert get_db().execute("SELECT COUNT(*) FROM releases").fetchone()[0] == 25


def test_about_page(client):
    html = client.get("/about").get_data(as_text=True)
    assert "System information" in html and "Build (commit)" in html


def test_unknown_url_returns_404_page(client):
    resp = client.get("/nope")
    assert resp.status_code == 404 and b"Page not found" in resp.data


def test_production_requires_secret_key(tmp_path):
    with pytest.raises(RuntimeError):
        make_app(tmp_path, APP_ENV="production", SECRET_KEY="")
