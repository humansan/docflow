"""Top-level orchestrator: document in, Markdown out.

Accepts any format PyMuPDF can open (PDF, XPS, EPUB, MOBI, FB2, CBZ, images). Ties
together preprocessing, the layout model (behind the ``LayoutModel`` seam), Markdown
assembly, and TOC generation. Holds no infrastructure — just a function.
"""

from __future__ import annotations

from collections.abc import Iterator
from dataclasses import dataclass
from pathlib import Path

import fitz  # PyMuPDF

from .assemble import assemble
from .models import get_model
from .models.base import LayoutModel
from .preprocess import DEFAULT_DPI, preprocess
from .toc import build_toc


# Extensions PyMuPDF can open; used to pick documents out of a folder.
SUPPORTED_SUFFIXES = {
    ".pdf", ".xps", ".oxps", ".epub", ".mobi", ".fb2", ".cbz", ".svg",
    ".png", ".jpg", ".jpeg", ".bmp", ".gif", ".tif", ".tiff",
    ".pnm", ".ppm", ".pgm", ".pbm",
}


@dataclass
class ConversionResult:
    markdown: str
    markdown_path: Path
    assets_dir: Path


def convert(
    source: str | Path,
    *,
    model: str | LayoutModel = "mock",
    dpi: int = DEFAULT_DPI,
    out_dir: str | Path = "out",
) -> ConversionResult:
    source = Path(source)
    out_dir = Path(out_dir)
    out_dir.mkdir(parents=True, exist_ok=True)

    # Name outputs after the source so a folder of documents doesn't collide:
    # report.pdf -> report_out.md + report_assets/.
    assets_name = f"{source.stem}_assets"
    layout_model = get_model(model) if isinstance(model, str) else model

    doc = fitz.open(source)
    try:
        pages, metas = preprocess(doc, dpi)
        layouts = layout_model.parse(pages)
        body, headings = assemble(doc, layouts, metas, out_dir, assets_name=assets_name)
    finally:
        doc.close()

    markdown = f"{build_toc(headings)}\n\n---\n\n{body}" if headings else body
    md_path = out_dir / f"{source.stem}_out.md"
    md_path.write_text(markdown, encoding="utf-8")

    return ConversionResult(
        markdown=markdown,
        markdown_path=md_path,
        assets_dir=out_dir / assets_name,
    )


def convert_path(
    source: str | Path,
    *,
    model: str | LayoutModel = "mock",
    dpi: int = DEFAULT_DPI,
    out_dir: str | Path = "out",
) -> Iterator[ConversionResult]:
    """Convert a single document, or every supported document in a folder.

    Yields one :class:`ConversionResult` per file, *as each file finishes* — by which
    point that file's ``.md`` and figure crops are already on disk. Streaming the
    results this way lets a caller report progress incrementally instead of waiting for
    the whole batch to complete. The layout model is resolved once and reused across all
    files (one Modal/Colab connection for the whole batch).

    Being a generator, the body (including the empty-folder check below) runs lazily on
    first iteration; wrap in ``list(...)`` if you need every result up front.
    """
    source = Path(source)
    layout_model = get_model(model) if isinstance(model, str) else model

    if source.is_dir():
        files = sorted(
            p
            for p in source.iterdir()
            if p.is_file() and p.suffix.lower() in SUPPORTED_SUFFIXES
        )
        if not files:
            raise ValueError(f"No supported documents found in {source}")
    else:
        files = [source]

    for f in files:
        yield convert(f, model=layout_model, dpi=dpi, out_dir=out_dir)
