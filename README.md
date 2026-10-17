# marker-llama: Use Marker without Docker

## Rationale

I'm a Windows user who don't want to install docker (well it's so much trouble...), and this is a self-use repo for making marker compatible with my machine.

[marker](https://www.github.com/datalab-to/marker) v2 runs its VLM (OCR / layout) through a local inference server. Upstream defaults NVIDIA GPUs to **vLLM inside Docker**; the `llamacpp` backend needs no Docker and works with the prebuilt `llama-server.exe`. This directory is that setup: **zero source patches**, config + tooling only.

## Layout

```
marker-llama/
  scripts/
    install.cmd          one-shot (re)installer
    fetch_gguf.py        GGUF prefetch via plain HTTPS (proxy-safe)
    surya_stop.cmd/.py   stop lingering surya background servers
    marker.cmd           launchers - env + forward to uv-tool exes
    marker_single.cmd    (same body, self-naming: %~n0 -> matching exe)
    marker_gui.cmd
    marker_server.cmd
  tests/                 synthetic conversion test + findings (see tests/README.md)
  out/                   local conversions, gitignored
```

## Install

```cmd
scripts\install.cmd
```

What it does (manual equivalent):

```cmd
:: stop lingering servers first or removal fails with os error 5
scripts\surya_stop.cmd
:: py3.13 pin: pillow<11 has no cp314 wheels; cu126 index: PyPI win torch is CPU-only
uv tool install --python 3.13 marker-pdf ^
  --extra-index-url https://download.pytorch.org/whl/cu126 ^
  --index-strategy unsafe-best-match
:: GGUF prefetch: huggingface_hub's xet client ignores HTTP(S)_PROXY on
:: Windows and stalls at 0 bytes; this fetches via plain HTTPS instead
python scripts\fetch_gguf.py
```

Prereqs: `uv` on PATH, NVIDIA driver, and a CUDA-build `llama-server.exe`.
Wrappers default to `%LOCALAPPDATA%\llama-cpp\llama-server.exe`; set
`LLAMA_CPP_BINARY` in your environment before launching to override.

## Usage

```cmd
scripts\marker_single.cmd input.pdf --output_dir out
scripts\marker_single.cmd input.pdf --output_dir out --mode fast   :: 44s vs 136s on the test doc
scripts\marker.cmd docs_dir --output_dir out                       :: batch dir
scripts\marker_gui.cmd                                             :: streamlit UI
```

Wrappers default `LLAMA_CPP_BINARY` (a preset value wins), set
`SURYA_INFERENCE_BACKEND=llamacpp`, `PYTHONUTF8=1`, then forward to the
uv-tool executables, so every marker subcommand keeps its normal CLI.

First run of `balanced` mode spawns `llama-server.exe` (loads ~1.5 GB GGUF
onto the GPU), converts, then exits cleanly. `fast` mode spawns lightweight
python servers instead (kept alive on purpose for reuse across runs).

Throughput on a T1000 4GB (balanced): text-layer PDFs run ~16-18 s/page;
scanned PDFs (no text layer, full-page VLM OCR) run ~160 s/page - a
300-page scan is an overnight job on this class of GPU. VRAM stays flat
around 0.8-0.9 GB throughout.

## Troubleshooting

| Symptom | Fix |
|---|---|
| `uv tool upgrade/uninstall` fails: `Access is denied (os error 5)` | run `scripts\surya_stop.cmd` first — persistent batch servers lock the venv |
| GGUF download hangs at 0 bytes | xet client ignores proxy; run `python scripts\fetch_gguf.py` |
| `pillow` source build failure | uv picked Python 3.14; reinstall with `--python 3.13` |
| llama-server OOM on 4 GB VRAM | uncomment `SURYA_INFERENCE_PARALLEL=2` / `SURYA_INFERENCE_CTX_SIZE=24576` in the wrappers |
| uv resolves CPU torch (check `torch.version.__version__` lacks `+cu126`) | missing `--index-strategy unsafe-best-match` or the cu126 extra index |
| log shows `Failed to stop llamacpp ... WinError 87` or `WinError 5` at the end of a run | harmless: surya's liveness probe uses POSIX-style `os.kill(pid, 0)`, which errors on Windows, but the preceding TerminateProcess already worked (process death verified on 4/4 long runs) |
| wrappers break on paths with spaces / CJK when called from git-bash | MSYS mangles quoting on its way into cmd; wrappers target native cmd/PowerShell. From git-bash call the exe directly: `env LLAMA_CPP_BINARY=... SURYA_INFERENCE_BACKEND=llamacpp marker_single.exe "file.pdf"` |

## Known limits (reproducible with `tests/test_safe.qd`, see `tests/README.md`)

- Cross-page tables: split into several fragments, and rows at the page
  boundary can vanish entirely.
- Table cells: text clipped or shuffled across columns; bold inside cells
  usually dropped (occasionally survives as `<b>` HTML).
- Fullwidth punctuation normalized to halfwidth in body text and fullwidth
  alphanumerics too - but fullwidth inside table cells is kept (inconsistent).
- Heading levels drift (mixed directions); generated heading numbers get
  baked into the text with occasional orphan duplicates.
- Extra spaces inserted at originally wrapped lines.
- Single scrollable (non-paged) PDFs can lose the document tail; prefer
  paged PDFs.
- These are marker v2 pdftext/table-reconstruction limits, not Windows-specific.

## License

MIT
