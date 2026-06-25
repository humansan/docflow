# Docflow

Document reflow to Markdown conversion tool - powered by a vision-language OCR model.
Accepts any format PyMuPDF can open: **PDF, XPS, EPUB, MOBI, FB2, CBZ, and images**.

This repository is currently in very early stages - only local conversion at the moment, with the model running in Google Colab.

## Quick start

```bash
uv sync

# Offline smoke test (no GPU, no network) - uses the placeholder layout model.
# The input can be a single document OR a folder (every supported file is converted):
uv run docflow convert path/to/file.pdf --model mock -o out/
uv run docflow convert path/to/folder/ --model mock -o out/

# Real conversion via a dots.mocr server running in Colab:
#   1. Run notebooks/dots_server.ipynb, copy the printed tunnel URL.
#   2. set DOCFLOW_DOTS_URL=<that url>   (PowerShell: $env:DOCFLOW_DOTS_URL="<url>")
uv run docflow convert path/to/file.pdf --model dots -o out/

# Or via the deployed Modal GPU function (see .docs/PHASE1_GUIDE.md):
uv run docflow convert path/to/file.pdf --model modal -o out/
```

Each input `name.pdf` produces `out/name_out.md` with its figures under `out/name_assets/`,
so converting a whole folder never overwrites or collides.

## How it works

```
document ──> preprocess (PyMuPDF: render pages to images)
         ──> LayoutModel.parse (images -> layout JSON, in reading order)
         ──> assemble (layout JSON -> Markdown, crop figures to PNG)
         ──> <name>_out.md + <name>_assets/
```

Because everything downstream works on rendered page images, any input format PyMuPDF
supports works unchanged. Reflowable formats (EPUB/MOBI/FB2) are given a standard page
size during preprocessing.

The `LayoutModel` seam (`src/docflow/models/base.py`) is the swappable boundary: `mock`
(offline development), `dots` (a remote dots.mocr server in Colab), and `modal` (a deployed
Modal GPU function) - all returning the same layout contract.
