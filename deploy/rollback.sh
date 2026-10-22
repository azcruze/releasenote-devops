#!/usr/bin/env bash
# Manual rollback on the VM.  Usage:
#   sudo bash rollback.sh --list          show releases (newest first) and the active one
#   sudo bash rollback.sh                 switch to the release before the active one
#   sudo bash rollback.sh <release_id>    switch to a specific release
# Rolls back CODE only. The SQLite database is NOT reverted; see docs/PIPELINE.md.
set -Eeuo pipefail
APP_ROOT=/opt/releasenote; RELEASES="$APP_ROOT/releases"; CURRENT="$APP_ROOT/current"
[[ $EUID -eq 0 ]] || { echo "Run with sudo." >&2; exit 1; }
active="$(readlink -f "$CURRENT" 2>/dev/null || true)"
mapfile -t all < <(ls -1dt "$RELEASES"/*/ | sed 's:/$::')
if [[ "${1:-}" == "--list" ]]; then
  for r in "${all[@]}"; do printf '%s %s\n' "$([[ $r == "$active" ]] && echo '*' || echo ' ')" "$(basename "$r")"; done; exit 0
fi
target=""
if [[ -n "${1:-}" ]]; then target="$RELEASES/$1"
else for i in "${!all[@]}"; do [[ "${all[$i]}" == "$active" ]] && target="${all[$((i+1))]:-}"; done; fi
[[ -n "$target" && -d "$target" ]] || { echo "No such release to roll back to." >&2; exit 1; }
echo "Switching $(basename "$active") -> $(basename "$target")"
ln -sfn "$target" "$APP_ROOT/current.tmp"; mv -T "$APP_ROOT/current.tmp" "$CURRENT"
systemctl restart releasenote
for _ in $(seq 1 20); do
  curl -fsS --max-time 3 http://127.0.0.1:8000/health | grep -Eq '"status": ?"ok"' && { echo "Healthy after rollback."; exit 0; }; sleep 2
done
echo "Service not healthy: journalctl -u releasenote -n 50" >&2; exit 1
