"""Operational commands:  flask --app wsgi <command>"""
import sqlite3
from pathlib import Path

import click
from flask import current_app
from werkzeug.security import generate_password_hash

from . import db


def register(app):
    @app.cli.command("init-db")
    def init_db_cmd():
        """Create the schema if it does not exist (idempotent)."""
        db.init_db()
        click.echo("Database ready.")

    @app.cli.command("seed-demo")
    def seed_cmd():
        """Add demo releases; versions that already exist are skipped."""
        click.echo(f"Inserted {db.seed_demo()} demo release(s).")

    @app.cli.command("reset-demo")
    @click.option("--yes", is_flag=True, help="Confirm deletion of ALL releases.")
    def reset_cmd(yes):
        """Delete every release and re-create the demo data."""
        if current_app.config["APP_ENV"] != "development":
            raise click.ClickException("reset-demo is allowed only when APP_ENV=development.")
        if not yes:
            raise click.UsageError("This deletes all releases. Re-run with --yes to confirm.")
        click.echo(f"Database reset; {db.reset_demo()} demo release(s) inserted.")

    @app.cli.command("backup-db")
    @click.argument("destination", type=click.Path(dir_okay=False))
    def backup_cmd(destination):
        """Consistent online backup of the SQLite database (safe while running)."""
        Path(destination).parent.mkdir(parents=True, exist_ok=True)
        src = sqlite3.connect(current_app.config["DATABASE_PATH"])
        dst = sqlite3.connect(destination)
        with dst:
            src.backup(dst)
        src.close()
        dst.close()
        click.echo(f"Backup written to {destination}")

    @app.cli.command("hash-password")
    def hash_cmd():
        """Print a hash to use as ADMIN_PASSWORD_HASH."""
        pw = click.prompt("Password", hide_input=True, confirmation_prompt=True)
        if len(pw) < 10:
            raise click.UsageError("Use at least 10 characters.")
        click.echo(generate_password_hash(pw))
