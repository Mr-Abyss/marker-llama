@echo off
rem Stop all persistent surya/marker background inference servers.
rem Reads pid from each sentinel json (~/.cache/datalab/surya/*_server.json),
rem kills the process tree (server spawns child workers), removes the sentinel.
rem Use this before `uv tool upgrade/uninstall marker-pdf` - lingering servers
rem lock the venv and make removal fail with "Access is denied" (os error 5).
rem surya_stop.py verifies each pid is really a surya process before killing
rem (stale sentinels + Windows PID reuse would otherwise hit innocent processes).
python "%~dp0surya_stop.py"

