#!/usr/bin/env bash
# Runs ON the Azure VM as root (Jenkins calls it with sudo).
# Usage: deploy.sh <staging_dir_with_unpacked_release> <release_id>
#
# Layout:  /opt/releasenote/releases/<id>/   code + its own virtualenv (kept: last 5)
#          /opt/releasenote/current          symlink to the active release
#          /var/lib/releasenote/             SQLite data (never touched by a deploy)
#          /etc/releasenote/releasenote.env  secrets/config (created once, never overwritten)
set -Eeuo pipefail

STAGE="${1:?staging dir required}"
RELEASE_ID="${2:?release id required}"
APP_USER=releasenote
APP_ROOT=/opt/releasenote
RELEASES="$APP_ROOT/releases"
CURRENT="$APP_ROOT/current"
DATA_DIR=/var/lib/releasenote
ENV_DIR=/etc/releasenote
ENV_FILE="$ENV_DIR/releasenote.env"
BACKUP_DIR=/var/backups/releasenote
SERVICE=releasenote
HEALTH_URL="http://127.0.0.1:8000/health"
KEEP_RELEASES=5
SWITCHED=0
PREVIOUS=""

log() { printf '[deploy %s] %s\n' "$(date -u +%H:%M:%S)" "$*"; }
[[ $EUID -eq 0 ]] || { echo "deploy.sh must run as root" >&2; exit 1; }
[[ "$RELEASE_ID" =~ ^[A-Za-z0-9._-]+$ ]] || { echo "invalid release id" >&2; exit 1; }
[[ -f "$STAGE/wsgi.py" ]] || { echo "staging dir does not contain the application" >&2; exit 1; }

wait_healthy() {            # up to ~40 s for the service to answer /health with status ok
  local i
  for i in $(seq 1 20); do
    if curl -fsS --max-time 3 "$HEALTH_URL" 2>/dev/null | grep -Eq '"status": ?"ok"'; then return 0; fi
    sleep 2
  done
  return 1
}

rollback() {
  if [[ -n "$PREVIOUS" && -d "$PREVIOUS" ]]; then
    log "ROLLBACK: restoring $PREVIOUS"
    ln -sfn "$PREVIOUS" "$APP_ROOT/current.tmp" && mv -T "$APP_ROOT/current.tmp" "$CURRENT"
    systemctl restart "$SERVICE" || true
    wait_healthy && log "Rollback complete: previous release is healthy." || log "Rollback finished but health check still failing - inspect: journalctl -u $SERVICE"
  else
    log "No previous release to roll back to."
  fi
}

trap 'rc=$?; log "FAILED at line $LINENO (exit $rc)"; if [[ $SWITCHED -eq 1 ]]; then rollback; fi; exit $rc' ERR

log "Step 1/9 - prerequisites"
command -v cloud-init >/dev/null 2>&1 && cloud-init status --wait >/dev/null 2>&1 || true
if ! dpkg -s nginx python3-venv python3-pip curl sqlite3 >/dev/null 2>&1; then
  log "Installing missing packages"
  export DEBIAN_FRONTEND=noninteractive
  apt-get update -y && apt-get install -y nginx python3-venv python3-pip curl sqlite3
fi

log "Step 2/9 - service account and directories"
id -u "$APP_USER" >/dev/null 2>&1 || useradd --system --home-dir "$APP_ROOT" --shell /usr/sbin/nologin "$APP_USER"
install -d -m 755 "$APP_ROOT" "$RELEASES"
install -d -m 750 -o "$APP_USER" -g "$APP_USER" "$DATA_DIR"
install -d -m 750 -o root -g "$APP_USER" "$ENV_DIR"
install -d -m 750 -o root -g root "$BACKUP_DIR"

log "Step 3/9 - environment file (created once, never overwritten)"
if [[ ! -f "$ENV_FILE" ]]; then
  ( umask 027
    cat > "$ENV_FILE" <<ENVEOF
APP_ENV=production
DATABASE_PATH=$DATA_DIR/releasenote.db
SECRET_KEY=$(python3 -c 'import secrets; print(secrets.token_hex(32))')
ADMIN_PASSWORD_HASH=''
AUTO_SEED=true
SESSION_COOKIE_SECURE=false
ENVEOF
  )
  chown root:"$APP_USER" "$ENV_FILE"; chmod 640 "$ENV_FILE"
  log "Created $ENV_FILE - the app is READ-ONLY until ADMIN_PASSWORD_HASH is set (see README)."
fi

log "Step 4/9 - install release $RELEASE_ID"
NEW="$RELEASES/$RELEASE_ID"
rm -rf "$NEW"; mkdir -p "$NEW"
cp -a "$STAGE"/. "$NEW"/
python3 -m venv "$NEW/venv"
"$NEW/venv/bin/pip" install --quiet --disable-pip-version-check --upgrade pip
"$NEW/venv/bin/pip" install --quiet --disable-pip-version-check -r "$NEW/requirements.txt"
chown -R root:root "$NEW"; chmod -R go-w "$NEW"

run_as_app() {   # run a flask CLI command as the service user inside the new release
  sudo -u "$APP_USER" bash -c 'set -a; . "$1"; set +a; cd "$2"; shift 2; exec ./venv/bin/flask --app wsgi "$@"' _ "$ENV_FILE" "$NEW" "$@"
}

log "Step 5/9 - smoke test new code and initialise schema (idempotent, no data loss)"
run_as_app init-db

log "Step 6/9 - back up the database"
if [[ -f "$DATA_DIR/releasenote.db" ]]; then
  run_as_app backup-db "$BACKUP_DIR/releasenote-$RELEASE_ID.db" || cp -a "$DATA_DIR/releasenote.db" "$BACKUP_DIR/releasenote-$RELEASE_ID.db"
  ls -1t "$BACKUP_DIR"/releasenote-*.db 2>/dev/null | tail -n +11 | xargs -r rm -f
fi

log "Step 7/9 - install systemd unit and Nginx site"
install -m 644 "$NEW/deploy/releasenote.service" /etc/systemd/system/releasenote.service
install -m 755 "$NEW/deploy/manage.sh" /usr/local/bin/releasenote-manage
install -m 644 "$NEW/deploy/nginx-releasenote.conf" /etc/nginx/sites-available/releasenote
ln -sfn /etc/nginx/sites-available/releasenote /etc/nginx/sites-enabled/releasenote
rm -f /etc/nginx/sites-enabled/default
nginx -t
systemctl daemon-reload
systemctl enable "$SERVICE" nginx >/dev/null 2>&1

log "Step 8/9 - switch to the new release and restart"
[[ -L "$CURRENT" ]] && PREVIOUS="$(readlink -f "$CURRENT")" || true
ln -sfn "$NEW" "$APP_ROOT/current.tmp"; mv -T "$APP_ROOT/current.tmp" "$CURRENT"
SWITCHED=1
systemctl restart "$SERVICE"
systemctl reload nginx || systemctl restart nginx
wait_healthy
log "Service healthy: $(curl -fsS --max-time 3 "$HEALTH_URL")"

log "Step 9/9 - prune old releases (keeping $KEEP_RELEASES)"
ls -1dt "$RELEASES"/*/ 2>/dev/null | tail -n +$((KEEP_RELEASES + 1)) | while read -r old; do
  old="${old%/}"
  [[ "$old" == "$(readlink -f "$CURRENT")" || "$old" == "$PREVIOUS" ]] || rm -rf "$old"
done
rm -rf "$STAGE"
log "Deployment of $RELEASE_ID complete."
