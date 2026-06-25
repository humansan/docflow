"""Top-level orchestrator: PDF in, Markdown out.

Ties together preprocessing, the layout model (behind the ``LayoutModel`` seam),
Markdown assembly, and TOC generation. Holds no infrastructure — just a function.
"""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

import fitz  # PyMuPDF

from .assemble import assemble
from .models import get_model
from .models.base import LayoutModel
from .preprocess import DEFAULT_DPI, preprocess
from .toc import build_toc


@dataclass
class ConversionResult:
    markdown: str
    markdown_path: Path
    assets_dir: Path


def convert(
    pdf_path: str | Path,
    *,
    model: str | LayoutModel = "mock",
    dpi: int = DEFAULT_DPI,
    out_dir: str | Path = "out",
) -> ConversionResult:
    pdf_path = Path(pdf_path)
    out_dir = Path(out_dir)
    out_dir.mkdir(parents=True, exist_ok=True)

    layout_model = get_model(model) if isinstance(model, str) else model

    doc = fitz.open(pdf_path)
    try:
        pages, metas = preprocess(doc, dpi)
        layouts = layout_model.parse(pages)
        body, headings = assemble(doc, layouts, metas, out_dir)
    finally:
        doc.close()

    markdown = f"{build_toc(headings)}\n\n---\n\n{body}" if headings else body
    md_path = out_dir / "result.md"
    md_path.write_text(markdown, encoding="utf-8")

    return ConversionResult(
        markdown=markdown,
        markdown_path=md_path,
        assets_dir=out_dir / "assets",
    )
