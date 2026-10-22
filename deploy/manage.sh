#!/usr/bin/env bash
# Installed as /usr/local/bin/releasenote-manage. Runs the Flask CLI as the service user
# with the production environment.   Usage: sudo releasenote-manage seed-demo
set -euo pipefail
[[ $EUID -eq 0 ]] || { echo "Run with sudo." >&2; exit 1; }
exec sudo -u releasenote bash -c 'set -a; . /etc/releasenote/releasenote.env; set +a
  cd /opt/releasenote/current && exec ./venv/bin/flask --app wsgi "$@"' _ "$@"
