"""Server-side validation and normalisation of release form data."""
import re
from datetime import date

from . import models

VERSION_RE = re.compile(r"^\d{1,4}\.\d{1,4}\.\d{1,4}(?:-[0-9A-Za-z][0-9A-Za-z.-]{0,30})?$")
_CTRL = re.compile(r"[\x00-\x08\x0b\x0c\x0e-\x1f\x7f]")


def _clean(value, multiline=False) -> str:
    value = _CTRL.sub("", (value or "").replace("\r\n", "\n").replace("\r", "\n")).strip()
    return value if multiline else " ".join(value.split())


def validate_release(form, existing_id=None):
    """Return (cleaned_data, errors). `errors` maps field name -> message."""
    d = {
        "version": re.sub(r"^[vV](?=\d)", "", _clean(form.get("version"))),
        "title": _clean(form.get("title")),
        "description": _clean(form.get("description")),
        "release_date": _clean(form.get("release_date")),
        "status": _clean(form.get("status")),
        "category": _clean(form.get("category")),
        "features": _clean(form.get("features"), True),
        "bug_fixes": _clean(form.get("bug_fixes"), True),
        "improvements": _clean(form.get("improvements"), True),
        "deployment_notes": _clean(form.get("deployment_notes"), True),
        "author": _clean(form.get("author")),
    }
    e = {}
    if not d["version"]:
        e["version"] = "Enter a version number."
    elif not VERSION_RE.match(d["version"]):
        e["version"] = "Use semantic versioning, for example 1.4.0 or 2.0.0-rc1."
    elif models.version_exists(d["version"], existing_id):
        e["version"] = f"Version {d['version']} already exists. Choose a different version."
    if not 3 <= len(d["title"]) <= 120:
        e["title"] = "Enter a title of 3 to 120 characters."
    if not 10 <= len(d["description"]) <= 1000:
        e["description"] = "Enter a description of 10 to 1000 characters."
    try:
        parsed = date.fromisoformat(d["release_date"])
        if not date(2000, 1, 1) <= parsed <= date(2100, 12, 31):
            raise ValueError
    except ValueError:
        e["release_date"] = "Enter a valid date between 2000 and 2100."
    if d["status"] not in models.STATUSES:
        e["status"] = "Choose a status from the list."
    if d["category"] not in models.CATEGORIES:
        e["category"] = "Choose a category from the list."
    if not 2 <= len(d["author"]) <= 80:
        e["author"] = "Enter the author's name (2 to 80 characters)."
    for field, label in (("features", "Features"), ("bug_fixes", "Bug fixes"),
                         ("improvements", "Improvements"), ("deployment_notes", "Deployment notes")):
        if len(d[field]) > 4000:
            e[field] = f"{label} must be 4000 characters or fewer."
    if not (d["features"] or d["bug_fixes"] or d["improvements"]) and "features" not in e:
        e["features"] = "Describe at least one feature, bug fix or improvement."
    return d, e
