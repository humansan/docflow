# Docflow

Document reflow to Markdown conversion tool - powered by a vision-language OCR model.
Accepts any format PyMuPDF can open: **PDF, XPS, EPUB, MOBI, FB2, CBZ, and images**.

This repository is currently in very early stages - only local conversion at the moment, with the model running in Google Colab.

## Quick start

```bash
uv sync

# Offline smoke test (no GPU, no network) - uses the placeholder layout model:
uv run docflow convert path/to/file.pdf --model mock -o out/

# Real conversion via a dots.mocr server running in Colab:
#   1. Run notebooks/dots_server.ipynb, copy the printed tunnel URL.
#   2. set DOCFLOW_DOTS_URL=<that url>   (PowerShell: $env:DOCFLOW_DOTS_URL="<url>")
uv run docflow convert path/to/file.pdf --model dots -o out/
```

Output lands in `out/result.md` with extracted figures under `out/assets/`.

## How it works

```
document ──> preprocess (PyMuPDF: render pages to images)
         ──> LayoutModel.parse (images -> layout JSON, in reading order)
         ──> assemble (layout JSON -> Markdown, crop figures to PNG)
         ──> result.md + assets/
```

Because everything downstream works on rendered page images, any input format PyMuPDF
supports works unchanged. Reflowable formats (EPUB/MOBI/FB2) are given a standard page
size during preprocessing.

The `LayoutModel` seam (`src/docflow/models/base.py`) is the swappable boundary: a `mock`
implementation for offline development, a `dots` implementation that calls a remote dots.mocr
server today, and a Modal implementation later - all returning the same layout contract.
