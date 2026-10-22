import pytest

from conftest import VALID, post


@pytest.mark.parametrize("field,value,fragment", [
    ("version", "", b"Enter a version"),
    ("version", "1.2", b"semantic versioning"),
    ("version", "abc", b"semantic versioning"),
    ("version", "1.2.3; DROP TABLE releases", b"semantic versioning"),
    ("title", "ab", b"title of 3 to 120"),
    ("description", "short", b"description of 10 to 1000"),
    ("release_date", "2026-13-45", b"valid date"),
    ("release_date", "", b"valid date"),
    ("status", "Hacked", b"Choose a status"),
    ("category", "Nonsense", b"Choose a category"),
    ("author", "", b"author"),
])
def test_invalid_field_rejected(admin, field, value, fragment):
    resp = post(admin, "/releases/new", {**VALID, field: value})
    assert resp.status_code == 422
    assert fragment in resp.data


def test_requires_at_least_one_change(admin):
    resp = post(admin, "/releases/new", {**VALID, "features": "", "bug_fixes": "", "improvements": ""})
    assert resp.status_code == 422 and b"at least one feature" in resp.data


def test_overlong_notes_rejected(admin):
    resp = post(admin, "/releases/new", {**VALID, "deployment_notes": "x" * 4001})
    assert resp.status_code == 422


def test_duplicate_version_rejected(admin):
    assert post(admin, "/releases/new", VALID).status_code == 302
    dup = post(admin, "/releases/new", VALID)
    assert dup.status_code == 422 and b"already exists" in dup.data


def test_invalid_input_keeps_user_values(admin):
    resp = post(admin, "/releases/new", {**VALID, "version": "bad", "title": "Keep this title"})
    assert b"Keep this title" in resp.data
