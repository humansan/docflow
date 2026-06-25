"""Assemble layout JSON into Markdown.

Walks every page's elements in reading order and maps each category to Markdown.
Headings are also collected so :mod:`docflow.toc` can build a clickable TOC.
Pictures are cropped to PNG via :mod:`docflow.figures`. Page headers/footers are
dropped; footnotes are gathered and appended at the end.
"""

from __future__ import annotations

import re
from pathlib import Path

import fitz  # PyMuPDF

from . import figures
from .models.base import Category, PageLayout
from .preprocess import PageMeta

HEADING_LEVELS = {Category.TITLE: 1, Category.SECTION_HEADER: 2}
DROP = {Category.PAGE_HEADER, Category.PAGE_FOOTER}
_LIST_MARKERS = ("-", "*", "+")
_HEADING_RE = re.compile(r"^\s*(#{1,6})\s+(.*)$", re.DOTALL)


def _clean(text: str | None) -> str:
    return (text or "").strip()


def _heading(raw: str | None, default_level: int) -> tuple[int, str]:
    """Resolve a heading's level and text.

    dots.mocr emits Markdown directly, so a heading element's text often already
    starts with its own ``#``/``##``. Trust those (so we don't produce ``## ## Title``),
    falling back to the category's default level only when no prefix is present.
    """
    text = _clean(raw)
    m = _HEADING_RE.match(text)
    if m:
        return len(m.group(1)), m.group(2).strip()
    return default_level, text


def _as_list_item(text: str) -> str:
    stripped = text.lstrip()
    if stripped.startswith(_LIST_MARKERS) or (
        stripped[:2].rstrip(".").isdigit() and "." in stripped[:3]
    ):
        return text
    return f"- {text}"


def assemble(
    doc: fitz.Document,
    layouts: list[PageLayout],
    metas: list[PageMeta],
    out_dir: Path,
) -> tuple[str, list[tuple[int, str]]]:
    meta_by_page = {m.page_index: m for m in metas}
    blocks: list[str] = []
    headings: list[tuple[int, str]] = []
    footnotes: list[str] = []
    fig_count = 0

    for layout in layouts:
        meta = meta_by_page[layout.page_index]
        for el in layout.elements:
            cat = el.category
            if cat in DROP:
                continue
            if cat in HEADING_LEVELS:
                level, text = _heading(el.text, HEADING_LEVELS[cat])
                blocks.append(f"{'#' * level} {text}")
                headings.append((level, text))
            elif cat is Category.TEXT:
                blocks.append(_clean(el.text))
            elif cat is Category.LIST_ITEM:
                blocks.append(_as_list_item(_clean(el.text)))
            elif cat is Category.FORMULA:
                blocks.append(f"$$\n{_clean(el.text)}\n$$")
            elif cat is Category.TABLE:
                blocks.append(_clean(el.text))  # dots.ocr emits HTML; Markdown renders it
            elif cat is Category.CAPTION:
                blocks.append(f"*{_clean(el.text)}*")
            elif cat is Category.PICTURE:
                fig_count += 1
                rel = Path("assets") / f"page{layout.page_index}_fig{fig_count}.png"
                figures.crop_figure(doc, el, meta, out_dir / rel)
                blocks.append(f"![Figure]({rel.as_posix()})")
            elif cat is Category.FOOTNOTE:
                footnotes.append(_clean(el.text))
            else:  # defensive: unknown category -> treat as text
                if el.text:
                    blocks.append(_clean(el.text))

    body = "\n\n".join(b for b in blocks if b)
    if footnotes:
        notes = "\n".join(f"[^{i + 1}]: {f}" for i, f in enumerate(footnotes))
        body = f"{body}\n\n---\n\n{notes}"
    return body, headings
