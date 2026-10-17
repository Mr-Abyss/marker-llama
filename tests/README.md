# Conversion test

Synthetic test document (no real data) reproducing marker's known conversion
defects on the Windows/llamacpp backend.

## Files

- `test_safe.qd` - quarkdown source (34-row table with bold + fullwidth
  punctuation in cells, multi-level headings, long wrapped paragraphs,
  fullwidth alphanumerics). `.doctype {paged}` is required: without it
  quarkdown emits a single scrollable PDF page, which skips the cross-page
  table case and triggers a separate tail-truncation bug.
- `test_safe.pdf` - compiled with quarkdown + Edge headless.
- `marker_output/test_safe/` - marker balanced-mode output (committed as evidence).

## Regenerate

```cmd
:: PDF (Edge path may differ; any Chromium works)
quarkdown c tests\test_safe.qd -o tests --out-name test_safe --pdf ^
  --chrome-path "C:\Program Files (x86)\Microsoft\Edge\Application\msedge.exe"

:: marker conversion (balanced)
scripts\marker_single.cmd tests\test_safe.pdf --output_dir tests\marker_output
```

Latest run: marker 2.x, llamacpp backend, 109 s, 4 pages.

## Findings

Reproduced (matches README "Known limits"):

| Defect | Evidence in output |
|---|---|
| Cross-page table split | one source table -> 4 markdown fragments |
| Cell text clipped / shuffled across columns | most table rows column-misaligned |
| Bold inside table cells | only the pre-page-break row keeps it (as `<b>` HTML); all other rows lose it |
| Fullwidth -> halfwidth | body text `，：；？！（）～` -> `,:;?!()~`; fullwidth `１２３ＡＢＣ` -> `123ABC` - but fullwidth inside table cells is kept (inconsistent) |
| Heading level drift | mixed directions: `##` -> `#`, `##` -> `###`; quarkdown's auto numbers ("1.1") baked into heading text, plus one orphan "1.1" line |
| Spurious spaces at wrapped lines | "方 括号", "原本连续 的行", "英文半角 对照" |

Additional findings not in the README yet:

- Rows falling on the page boundary vanish entirely (rows 02, 16, 26, 33 lost).
- On a single scrollable (non-paged) PDF, marker truncated the document tail
  (everything after the table's last row was dropped). Paged PDFs are
  unaffected - prefer paged output when converting quarkdown documents.

Text fidelity outside tables and headings is otherwise verbatim.
