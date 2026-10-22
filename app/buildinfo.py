"""Resolve a build identifier without ever failing application start-up."""
import os
import subprocess
from pathlib import Path


def read_build_info(base_dir: Path) -> dict:
    info = {"commit": "", "build_number": "", "built_at": ""}
    path = base_dir / "BUILD_INFO"           # written by the Jenkins packaging stage
    if path.is_file():
        for line in path.read_text(encoding="utf-8", errors="ignore").splitlines():
            key, _, value = line.partition("=")
            if key.strip() in info:
                info[key.strip()] = value.strip()[:64]
    if not info["commit"]:
        info["commit"] = os.environ.get("GIT_COMMIT", "")[:12]
    if not info["commit"] and (base_dir / ".git").exists():
        try:
            out = subprocess.run(["git", "rev-parse", "--short=8", "HEAD"], cwd=base_dir,
                                 capture_output=True, text=True, timeout=2, check=True)
            info["commit"] = out.stdout.strip()
        except (OSError, subprocess.SubprocessError):
            pass
    info["commit"] = info["commit"] or "unknown"
    return info
