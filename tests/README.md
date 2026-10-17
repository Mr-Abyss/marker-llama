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

## Scanned-book OCR test (no text layer)

Corpus: public-domain strength-training books placed in this directory.

- `Secrets Of Strength -- Earle Liederman -- 1925.pdf` (201 pages, 15.5 MB)
- `Sandow's System of Physical Training -- Eugen Sandow -- 1894.pdf` (not yet converted)

`secrets1925.pdf` is a space-free copy of the 1925 book used for the CLI run -
quoted paths with spaces get mangled when wrappers are called from git-bash
(MSYS quote conversion; see README troubleshooting).

Run (pages 1-10: frontispiece, preface, contents, illustration list,
introduction start), balanced mode, T1000 4GB:

```cmd
scripts\marker_single.cmd tests\secrets1925.pdf --output_dir tests\marker_output_ocr --page_range 0-9
```

Latest run: 1309 s total, **131 s/page** (full 201-page book extrapolates to
~7.3 h). VRAM flat. One photo extracted to `_page_0_Picture_2.jpeg`.

Findings (scan OCR path):

| Aspect | Result |
|---|---|
| Body text | fluent and near-verbatim; old-style spacing ("book ;") and quote styles preserved |
| Structure | PREFACE / CONTENTS / INTRODUCTION headings recovered in order |
| Printed TOC + illustration list | reconstructed as markdown tables incl. page-number column - usable, but dot leaders kept as literal ". . . . ." noise, and layout-table detection confirms the "layout read as table" detector trait |
| Italics inside tables | survive as `<i>` HTML (same tag-residue pattern as `<b>` in test_safe) |
| Proper nouns | occasional single-letter slips: "LURICII" (Lurich), "NORDQUES" (Nordquest) |
| Paragraph flow | one page-boundary paragraph split into two blocks |

Overall: scan path output is reading-quality; expect per-book a handful of
proper-noun slips and cosmetic table noise, not content loss.
