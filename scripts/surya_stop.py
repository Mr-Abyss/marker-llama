"""Stop persistent surya/marker background inference servers on Windows.

Reads each sentinel json (~/.cache/datalab/surya/*_server.json), verifies the
pid actually belongs to a surya/marker process (stale sentinels + PID reuse
would otherwise kill an innocent process), then kills the tree and removes
the sentinel. Run before `uv tool upgrade/uninstall marker-pdf` - lingering
servers lock the venv and break removal with "Access is denied" (os error 5).
"""

import glob
import json
import os
import subprocess
from pathlib import Path

SENTINEL_GLOB = "~/.cache/datalab/surya/*_server.json"
IDENTITY_MARKERS = ("surya", "marker-pdf", "ocr_error", "fast_layout", "detection")


def cmdline_of(pid: int) -> str:
    try:
        out = subprocess.run(
            ["wmic", "process", "where", f"processid={pid}", "get", "commandline"],
            capture_output=True,
            text=True,
            timeout=15,
        ).stdout
    except Exception:
        return ""
    return " ".join(out.split())


def is_surya_process(pid: int) -> bool:
    cmd = cmdline_of(pid)
    return any(marker in cmd for marker in IDENTITY_MARKERS)


def main() -> None:
    for sentinel in glob.glob(os.path.expanduser(SENTINEL_GLOB)):
        try:
            pid = json.load(open(sentinel)).get("pid")
        except Exception:
            pid = None
        if not pid:
            Path(sentinel).unlink(missing_ok=True)  # unreadable -> stale
            continue
        if not is_surya_process(pid):
            print(f"{Path(sentinel).name}: pid {pid} is not a surya process (stale sentinel), removing only")
        else:
            r = subprocess.run(["taskkill", "/T", "/F", "/PID", str(pid)], capture_output=True, text=True)
            print(f"{Path(sentinel).name}: taskkill pid {pid} -> {r.stdout.strip() or r.stderr.strip()}")
        Path(sentinel).unlink(missing_ok=True)
    print("surya servers stopped.")


if __name__ == "__main__":
    main()
