"""Central configuration. Every value comes from environment variables;
no secret is stored in source code."""
import os
from datetime import timedelta
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent


def _flag(name: str, default: bool = False) -> bool:
    return os.environ.get(name, str(default)).strip().lower() in {"1", "true", "yes", "on"}


class Config:
    APP_NAME = "ReleaseNote"
    APP_VERSION = "1.0.0"
    APP_ENV = os.environ.get("APP_ENV", "development").strip().lower()

    DATABASE_PATH = os.environ.get("DATABASE_PATH", str(BASE_DIR / "instance" / "releasenote.db"))
    SECRET_KEY = os.environ.get("SECRET_KEY", "")

    # Management (write) access. See docs/ARCHITECTURE.md -> Security model.
    ADMIN_PASSWORD = os.environ.get("ADMIN_PASSWORD", "")
    ADMIN_PASSWORD_HASH = os.environ.get("ADMIN_PASSWORD_HASH", "")

    AUTO_SEED = _flag("AUTO_SEED", True)    # insert any missing seeded versions
    BUILD_ID = os.environ.get("BUILD_ID", "")

    PER_PAGE = 8
    MAX_CONTENT_LENGTH = 64 * 1024
    SESSION_COOKIE_HTTPONLY = True
    SESSION_COOKIE_SAMESITE = "Lax"
    SESSION_COOKIE_SECURE = _flag("SESSION_COOKIE_SECURE")  # enable once HTTPS is configured
    PERMANENT_SESSION_LIFETIME = timedelta(hours=8)
