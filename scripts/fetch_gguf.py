"""Fetch surya VLM GGUFs into the HF cache via plain HTTPS (proxy-friendly).

The huggingface_hub/xet client ignores HTTP(S)_PROXY on Windows and stalls at
0 bytes; curl-style direct downloads work. Files land in the snapshot dir as
real files (no symlinks - Windows needs Developer Mode for those), where
hf_hub_download's fast path picks them up without touching the network.
"""

import os
import urllib.request
from pathlib import Path

REPO = "datalab-to/surya-ocr-2-gguf"
FILES = {"surya-2.gguf": 1266400864, "surya-2-mmproj.gguf": 204986688}


def snapshot_dir() -> Path:
    base = Path.home() / ".cache" / "huggingface" / "hub" / f"models--{REPO.replace('/', '--')}"
    refs = base / "refs" / "main"
    sha = refs.read_text().strip() if refs.exists() else None
    if not sha:  # never seen by hf before: materialize a refs/snapshots skeleton
        sha = "manual"
        (base / "refs").mkdir(parents=True, exist_ok=True)
        refs.write_text(sha + "\n")
    snap = base / "snapshots" / sha
    snap.mkdir(parents=True, exist_ok=True)
    return snap


def fetch(name: str, expect: int) -> None:
    dest = snapshot_dir() / name
    if dest.exists() and dest.stat().st_size == expect:
        print(f"{name}: already present ({expect} bytes)")
        return
    url = f"https://huggingface.co/{REPO}/resolve/main/{name}"
    print(f"{name}: downloading {url}")
    with urllib.request.urlopen(url) as r, open(dest, "wb") as f:
        while chunk := r.read(1 << 20):
            f.write(chunk)
    got = dest.stat().st_size
    if got != expect:
        dest.unlink(missing_ok=True)
        raise SystemExit(f"{name}: size mismatch, got {got}, expected {expect}")


if __name__ == "__main__":
    for fname, size in FILES.items():
        fetch(fname, size)
    print("GGUFs ready.")
