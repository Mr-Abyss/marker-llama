# marker-llama: Use Marker without Docker

## Rationale

I'm a Windows user who don't want to install docker (well it's so much trouble...), and this is a self-use repo for making marker compatible with my machine.

[marker](https://www.github.com/datalab-to/marker) v2 runs its VLM (OCR / layout) through a local inference server. Upstream defaults NVIDIA GPUs to **vLLM inside Docker**; the `llamacpp` backend needs no Docker and works with the prebuilt `llama-server.exe`. This directory is that setup: **zero source patches**, config + tooling only.

## Layout

```
marker-win/
  scripts/
    install.cmd          one-shot (re)installer
    fetch_gguf.py        GGUF prefetch via plain HTTPS (proxy-safe)
    surya_stop.cmd/.py   stop lingering surya background servers
    marker.cmd           launchers - env + forward to uv-tool exes
    marker_single.cmd    (same body, self-naming: %~n0 -> matching exe)
    marker_gui.cmd
    marker_server.cmd
  out/                   test conversions
  src/                   marker + surya clones, research only - DELETABLE
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

Prereqs: `uv` on PATH, NVIDIA driver, `llama-server.exe` (CUDA build) at
`C:\Users\Alex\AppData\Local\llama-cpp\llama-server.exe` — edit the wrappers
if that path changes.

## Usage

```cmd
scripts\marker_single.cmd input.pdf --output_dir out
scripts\marker_single.cmd input.pdf --output_dir out --mode fast   :: 44s vs 136s on the test doc
scripts\marker.cmd docs_dir --output_dir out                       :: batch dir
scripts\marker_gui.cmd                                             :: streamlit UI
```

Wrappers set `LLAMA_CPP_BINARY`, `SURYA_INFERENCE_BACKEND=llamacpp`,
`PYTHONUTF8=1`, then forward to the uv-tool executables, so every marker
subcommand keeps its normal CLI.

First run of `balanced` mode spawns `llama-server.exe` (loads ~1.5 GB GGUF
onto the GPU), converts, then exits cleanly. `fast` mode spawns lightweight
python servers instead (kept alive on purpose for reuse across runs).

## Troubleshooting

| Symptom | Fix |
|---|---|
| `uv tool upgrade/uninstall` fails: `Access is denied (os error 5)` | run `scripts\surya_stop.cmd` first — persistent batch servers lock the venv |
| GGUF download hangs at 0 bytes | xet client ignores proxy; run `python scripts\fetch_gguf.py` |
| `pillow` source build failure | uv picked Python 3.14; reinstall with `--python 3.13` |
| llama-server OOM on 4 GB VRAM | uncomment `SURYA_INFERENCE_PARALLEL=2` / `SURYA_INFERENCE_CTX_SIZE=24576` in the wrappers |
| uv resolves CPU torch (check `torch.version.__version__` lacks `+cu126`) | missing `--index-strategy unsafe-best-match` or the cu126 extra index |

## Known limits (observed on the quarkdown test doc)

- Large tables: occasionally split in two; right-column cell text can clip.
- Bold within table cells dropped; fullwidth punctuation normalized to halfwidth.
- These are marker v2 pdftext/table-reconstruction limits, not Windows-specific.
