"""SQLite connection handling, schema creation and demo data."""
import sqlite3
from datetime import datetime, timezone
from pathlib import Path

from flask import current_app, g

SCHEMA = """
CREATE TABLE IF NOT EXISTS releases (
    id               INTEGER PRIMARY KEY AUTOINCREMENT,
    version          TEXT NOT NULL UNIQUE,
    title            TEXT NOT NULL,
    description      TEXT NOT NULL DEFAULT '',
    release_date     TEXT NOT NULL,
    status           TEXT NOT NULL,
    category         TEXT NOT NULL,
    features         TEXT NOT NULL DEFAULT '',
    bug_fixes        TEXT NOT NULL DEFAULT '',
    improvements     TEXT NOT NULL DEFAULT '',
    deployment_notes TEXT NOT NULL DEFAULT '',
    author           TEXT NOT NULL,
    created_at       TEXT NOT NULL,
    updated_at       TEXT NOT NULL
);
CREATE INDEX IF NOT EXISTS idx_releases_date ON releases (release_date DESC, id DESC);
CREATE INDEX IF NOT EXISTS idx_releases_status ON releases (status);
"""


def utc_now() -> str:
    return datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M:%S")


def get_db() -> sqlite3.Connection:
    if "db" not in g:
        conn = sqlite3.connect(current_app.config["DATABASE_PATH"], timeout=10)
        conn.row_factory = sqlite3.Row
        g.db = conn
    return g.db


def close_db(_exc=None) -> None:
    conn = g.pop("db", None)
    if conn is not None:
        conn.close()


def init_db() -> None:
    """Create the schema and add compatible columns without changing existing rows."""
    Path(current_app.config["DATABASE_PATH"]).parent.mkdir(parents=True, exist_ok=True)
    db = get_db()
    db.executescript(SCHEMA)
    columns = {row["name"] for row in db.execute("PRAGMA table_info(releases)")}
    if "description" not in columns:
        db.execute("ALTER TABLE releases ADD COLUMN description TEXT NOT NULL DEFAULT ''")
    db.execute("PRAGMA journal_mode=WAL")
    db.commit()


DEMO_RELEASES = [
    dict(version="1.6.0", title="Release workspace launch", description="Introduces a unified workspace for reviewing product releases and their operational notes.", release_date="2024-01-18", status="Released", category="Major", author="ReleaseNote Demo Team", features="Central release history with semantic versions\nStructured release detail pages", bug_fixes="Corrected date ordering for releases created on the same day", improvements="Established a consistent release summary layout", deployment_notes=""),
    dict(version="1.6.1", title="Dashboard layout refinement", description="Improves the dashboard hierarchy so release health and recent activity are easier to scan.", release_date="2024-02-08", status="Released", category="Patch", author="ReleaseNote Demo Team", features="", bug_fixes="Fixed a narrow-screen overflow in the summary cards", improvements="Adjusted card spacing and heading contrast", deployment_notes=""),
    dict(version="1.6.2", title="Release form validation update", description="Adds clearer feedback for common release metadata validation errors.", release_date="2024-02-29", status="Released", category="Patch", author="ReleaseNote Demo Team", features="", bug_fixes="Preserved submitted form values when validation fails", improvements="Standardized field-level validation messages", deployment_notes=""),
    dict(version="1.7.0", title="Release history search", description="Makes it possible to locate releases by their version number or title.", release_date="2024-04-11", status="Released", category="Minor", author="ReleaseNote Demo Team", features="Search release versions and titles\nSupport a leading v in version searches", bug_fixes="", improvements="Added a useful no-results state", deployment_notes=""),
    dict(version="1.7.1", title="Search and filter corrections", description="Tightens search behavior and fixes edge cases when combining history filters.", release_date="2024-05-02", status="Released", category="Patch", author="ReleaseNote Demo Team", features="", bug_fixes="Kept percent and underscore characters literal in search\nCorrected combined status and category filters", improvements="Made filter reset behavior more predictable", deployment_notes=""),
    dict(version="1.8.0", title="Release category management", description="Adds consistent categories to help teams distinguish major, minor, patch, hotfix, and security releases.", release_date="2024-06-20", status="Released", category="Minor", author="ReleaseNote Demo Team", features="Added category badges to release listings\nAdded category selection to release forms", bug_fixes="", improvements="Improved scanability of the release history", deployment_notes=""),
    dict(version="1.8.1", title="API connector rollback", description="A sample integration change was rolled back after an upstream API contract changed.", release_date="2024-07-04", status="Rolled Back", category="Patch", author="ReleaseNote Demo Team", features="", bug_fixes="Restored the previous connector behavior after a response-format mismatch", improvements="Documented integration rollback considerations", deployment_notes=""),
    dict(version="1.9.0", title="Release activity reporting", description="Introduces a reporting view for summarizing release activity across the selected period.", release_date="2024-09-12", status="Released", category="Minor", author="ReleaseNote Demo Team", features="Added release status summary reporting\nAdded date-based activity views", bug_fixes="", improvements="Optimized aggregate queries for report summaries", deployment_notes=""),
    dict(version="1.9.1", title="Accessible navigation and labels", description="Improves keyboard and assistive-technology support across release management screens.", release_date="2024-10-03", status="Released", category="Patch", author="ReleaseNote Demo Team", features="", bug_fixes="Corrected missing form labels and pagination announcements", improvements="Improved focus visibility and semantic table headings", deployment_notes=""),
    dict(version="2.0.0", title="ReleaseNote 2.0 platform update", description="Refreshes the release workflow and data model for more complete, readable release records.", release_date="2025-01-16", status="Released", category="Major", author="ReleaseNote Demo Team", features="Added a release description field\nExpanded structured change and deployment notes", bug_fixes="Addressed several release form and detail rendering edge cases", improvements="Introduced a backward-compatible SQLite schema update", deployment_notes=""),
    dict(version="2.0.1", title="SQLite query performance", description="Reduces database work for frequently used dashboard and release-history queries.", release_date="2025-02-06", status="Released", category="Patch", author="ReleaseNote Demo Team", features="", bug_fixes="Avoided unnecessary repeated release lookups", improvements="Added and verified indexes for release date and status queries", deployment_notes=""),
    dict(version="2.0.2", title="Legacy export endpoint retirement", description="Marks a superseded sample export path as deprecated while the replacement workflow is adopted.", release_date="2025-03-06", status="Deprecated", category="Patch", author="ReleaseNote Demo Team", features="", bug_fixes="Clarified behavior for clients using the retired export route", improvements="Documented the supported reporting path", deployment_notes=""),
    dict(version="2.1.0", title="Release report exports", description="Adds practical export formats for sharing release information with delivery and support teams.", release_date="2025-05-15", status="Released", category="Minor", author="ReleaseNote Demo Team", features="Export release summaries as Markdown\nAdd CSV output for filtered release lists", bug_fixes="", improvements="Kept exported fields aligned with release detail pages", deployment_notes=""),
    dict(version="2.1.1", title="Session handling hardening", description="Strengthens administrator sign-in and session behavior for release-management actions.", release_date="2025-06-05", status="Released", category="Security", author="ReleaseNote Demo Team", features="", bug_fixes="Expired stale authentication sessions more consistently", improvements="Hardened session cookie defaults and login throttling", deployment_notes=""),
    dict(version="2.2.0", title="Audit history and change traceability", description="Improves visibility into when a release record was created and last updated.", release_date="2025-08-14", status="Released", category="Minor", author="ReleaseNote Demo Team", features="Display record creation and update timestamps\nClarify release ownership in details", bug_fixes="", improvements="Made release changes easier to review during handoffs", deployment_notes=""),
    dict(version="2.2.1", title="Deployment health-check rollback", description="A sample deployment reliability update was rolled back after its health probe timed out.", release_date="2025-09-04", status="Rolled Back", category="Patch", author="ReleaseNote Demo Team", features="", bug_fixes="Restored the previous health-check timeout behavior", improvements="Recorded a safer retry strategy for the follow-up change", deployment_notes=""),
    dict(version="2.3.0", title="External API integration framework", description="Adds a consistent foundation for connecting release workflows to external delivery APIs.", release_date="2025-11-13", status="Released", category="Minor", author="ReleaseNote Demo Team", features="Added configurable API integration settings\nRecorded integration outcomes in release notes", bug_fixes="", improvements="Kept integration failures isolated from core release management", deployment_notes=""),
    dict(version="2.3.1", title="Security patch for request handling", description="Addresses a sample security hardening item in release search and form processing.", release_date="2025-12-04", status="Released", category="Security", author="ReleaseNote Demo Team", features="", bug_fixes="Hardened validation for malformed release input", improvements="Retained parameterized database queries throughout the release workflow", deployment_notes=""),
    dict(version="2.4.0", title="Release insights dashboard", description="Expands dashboard summaries to make release status and delivery activity easier to monitor.", release_date="2026-02-12", status="Released", category="Minor", author="ReleaseNote Demo Team", features="Added recent release activity summaries\nImproved status distribution indicators", bug_fixes="", improvements="Improved dashboard query efficiency for larger histories", deployment_notes=""),
    dict(version="2.4.1", title="Database initialization reliability", description="Makes schema initialization repeatable and safer when a service starts against an existing database.", release_date="2026-03-05", status="Released", category="Patch", author="ReleaseNote Demo Team", features="", bug_fixes="Prevented repeated initialization from changing existing release records", improvements="Added a compatible schema migration check", deployment_notes=""),
    dict(version="2.4.2", title="Retire legacy session flow", description="Deprecates an older sample session flow in favor of the hardened administrator workflow.", release_date="2026-04-09", status="Deprecated", category="Security", author="ReleaseNote Demo Team", features="", bug_fixes="Clarified sign-in behavior for legacy sessions", improvements="Documented the supported session lifecycle", deployment_notes=""),
    dict(version="2.4.3", title="Release history performance tuning", description="Optimizes filtered history queries and improves the responsiveness of larger release lists.", release_date="2026-06-11", status="Released", category="Patch", author="ReleaseNote Demo Team", features="", bug_fixes="Fixed page clamping for filters with a reduced result set", improvements="Reduced time spent loading paginated release history", deployment_notes=""),
    dict(version="2.4.4", title="Deployment backup verification", description="Adds a planned deployment reliability improvement for confirming application data backups.", release_date="2026-10-29", status="Scheduled", category="Minor", author="ReleaseNote Demo Team", features="Verify the SQLite backup before switching application releases", bug_fixes="", improvements="Make rollback preparation more observable", deployment_notes=""),
    dict(version="2.4.5", title="Accessibility review follow-up", description="Tracks planned accessibility refinements identified during a sample interface review.", release_date="2026-11-05", status="Draft", category="Patch", author="ReleaseNote Demo Team", features="", bug_fixes="", improvements="Review keyboard interaction and improve status announcements", deployment_notes=""),
    dict(version="2.5.0", title="Release integrations and audit insights", description="Plans a broader update combining integration visibility with clearer release audit reporting.", release_date="2026-11-19", status="Scheduled", category="Minor", author="ReleaseNote Demo Team", features="Expand external API integration summaries\nAdd exportable audit reporting", bug_fixes="", improvements="Improve release traceability for delivery teams", deployment_notes=""),
]


def seed_demo(only_if_empty: bool = False) -> int:
    """Insert demo rows. INSERT OR IGNORE on the unique version prevents duplicates."""
    db = get_db()
    if only_if_empty and db.execute("SELECT COUNT(*) FROM releases").fetchone()[0] > 0:
        return 0
    now, inserted = utc_now(), 0
    for r in DEMO_RELEASES:
        cur = db.execute(
            """INSERT OR IGNORE INTO releases (version,title,description,release_date,status,category,features,
               bug_fixes,improvements,deployment_notes,author,created_at,updated_at)
               VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?)""",
            (r["version"], r["title"], r["description"], r["release_date"], r["status"],
             r["category"], r["features"],
             r["bug_fixes"], r["improvements"], r["deployment_notes"], r["author"], now, now))
        inserted += cur.rowcount
    db.commit()
    return inserted


def reset_demo() -> int:
    db = get_db()
    db.execute("DELETE FROM releases")
    db.execute("DELETE FROM sqlite_sequence WHERE name='releases'")
    db.commit()
    return seed_demo()


def init_app(app) -> None:
    app.teardown_appcontext(close_db)
