@echo off
rem One-shot installer: marker-pdf as uv tool, Windows-native, no docker.
rem Re-run safe. Run from anywhere. Requires: uv on PATH, NVIDIA driver, llama-server.exe.
rem
rem 1) persistent background servers may lock the old venv - stop them first
call "%~dp0surya_stop.cmd"

rem 2) (re)install marker-pdf pinned to py3.13 + CUDA torch (cu126 index has win wheels;
rem    PyPI windows torch is CPU-only; pillow<11 has no cp314 wheels so do NOT let uv pick 3.14)
uv tool install --python 3.13 marker-pdf ^
  --extra-index-url https://download.pytorch.org/whl/cu126 ^
  --index-strategy unsafe-best-match

rem 3) pre-fetch surya VLM GGUFs - hf/xet client ignores HTTP proxy and stalls at 0 bytes,
rem    so curl the files straight into the HF snapshot dir (plain HTTPS respects the proxy).
python "%~dp0fetch_gguf.py"

echo Done. Use: marker-win\scripts\marker_single.cmd input.pdf --output_dir out
