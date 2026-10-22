import re

import pytest

from conftest import PASSWORD, VALID, make_app, post, token


def test_security_headers_present(client):
    h = client.get("/").headers
    assert h["X-Content-Type-Options"] == "nosniff" and h["X-Frame-Options"] == "DENY"
    assert "default-src 'self'" in h["Content-Security-Policy"]


def test_writes_require_login_when_password_set(client):
    resp = client.get("/releases/new")
    assert resp.status_code == 302 and "/login" in resp.headers["Location"]


def test_post_without_csrf_token_rejected(admin):
    resp = admin.post("/releases/new", data=VALID)
    assert resp.status_code == 400


def test_post_with_wrong_csrf_token_rejected(admin):
    token(admin, "/releases/new")
    assert admin.post("/releases/new", data={**VALID, "csrf_token": "forged"}).status_code == 400


def test_delete_via_get_never_deletes(admin, seeded):
    admin.get("/releases/1/delete")
    assert admin.get("/releases/1").status_code == 200


def test_login_wrong_password(client):
    resp = post(client, "/login", {"password": "nope"})
    assert resp.status_code == 401 and b"Incorrect password" in resp.data


def test_login_throttle(client):
    for _ in range(5):
        post(client, "/login", {"password": "bad"})
    assert post(client, "/login", {"password": PASSWORD}).status_code == 429


def test_logout_revokes_access(admin):
    assert post(admin, "/logout", token_from="/").status_code == 302
    assert admin.get("/releases/new").status_code == 302


@pytest.mark.parametrize("target", ["https://evil.example", "//evil.example", "javascript:alert(1)"])
def test_open_redirect_blocked(client, target):
    resp = client.post("/login", data={"password": PASSWORD, "next": target,
                                       "csrf_token": token(client, "/login")})
    assert resp.status_code == 302 and "evil" not in resp.headers["Location"]


def test_hashed_password_supported(tmp_path):
    from werkzeug.security import generate_password_hash
    app = make_app(tmp_path, ADMIN_PASSWORD="", ADMIN_PASSWORD_HASH=generate_password_hash("a-long-password"))
    c = app.test_client()
    assert post(c, "/login", {"password": "wrong"}).status_code == 401
    assert post(c, "/login", {"password": "a-long-password"}).status_code == 302


def test_xss_is_escaped(admin):
    payload = "<script>alert(1)</script>"
    resp = post(admin, "/releases/new", {**VALID, "title": payload, "features": payload})
    page = admin.get(resp.headers["Location"]).get_data(as_text=True)
    assert payload not in page and "&lt;script&gt;" in page


def test_sql_injection_in_search_is_inert(client, seeded):
    resp = client.get("/releases?q=' OR 1=1 --")
    assert resp.status_code == 200 and "No releases match" in resp.get_data(as_text=True)
    assert client.get("/releases?status=Released' OR '1'='1").status_code == 200


def test_oversized_request_rejected(admin):
    resp = admin.post("/releases/new", data={"csrf_token": "x", "features": "a" * 70000})
    assert resp.status_code == 413


def test_production_without_password_is_read_only(tmp_path):
    app = make_app(tmp_path, APP_ENV="production", ADMIN_PASSWORD="", ADMIN_PASSWORD_HASH="")
    c = app.test_client()
    assert c.get("/").status_code == 200 and c.get("/health").status_code == 200
    assert c.get("/releases/new").status_code == 403


def test_open_mode_allows_local_development(tmp_path):
    app = make_app(tmp_path, ADMIN_PASSWORD="")
    c = app.test_client()
    assert post(c, "/releases/new", VALID).status_code == 302


def test_health_does_not_expose_secrets(client, app):
    body = client.get("/health").get_data(as_text=True)
    assert PASSWORD not in body and app.config["SECRET_KEY"] not in body
