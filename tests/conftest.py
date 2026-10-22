import re

import pytest

from app import create_app
from app.db import seed_demo

PASSWORD = "correct-horse-battery"

VALID = {
    "version": "3.0.0", "title": "Major redesign",
    "description": "A substantial redesign that improves release planning and review.",
    "release_date": "2026-09-01",
    "status": "Released", "category": "Major", "author": "Test Author",
    "features": "New dashboard\nNew search", "bug_fixes": "Fixed crash", "improvements": "Faster",
    "deployment_notes": "Restart service",
}


def make_app(tmp_path, **overrides):
    cfg = {"TESTING": True, "APP_ENV": "testing", "SECRET_KEY": "test-secret",
           "DATABASE_PATH": str(tmp_path / "test.db"), "ADMIN_PASSWORD": PASSWORD,
           "ADMIN_PASSWORD_HASH": "", "AUTO_SEED": False}
    cfg.update(overrides)
    return create_app(cfg)


def token(client, url):
    html = client.get(url).get_data(as_text=True)
    match = re.search(r'name="csrf_token" value="([^"]+)"', html)
    assert match, f"no CSRF token on {url}"
    return match.group(1)


def post(client, url, data=None, token_from=None):
    payload = dict(data or {})
    payload["csrf_token"] = token(client, token_from or url)
    return client.post(url, data=payload)


@pytest.fixture
def app(tmp_path):
    return make_app(tmp_path)


@pytest.fixture
def client(app):
    return app.test_client()


@pytest.fixture
def admin(client):
    resp = post(client, "/login", {"password": PASSWORD})
    assert resp.status_code == 302
    return client


@pytest.fixture
def seeded(app):
    with app.app_context():
        seed_demo()
    return app
