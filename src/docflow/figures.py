"""Figure extraction: crop a model's pixel bbox out of the PDF as a PNG.

The model returns bounding boxes in **image pixels**; PyMuPDF crops in **PDF
points**. :func:`bbox_to_rect` does the coordinate translation (kept pure so it
can be unit-tested without a document), and :func:`crop_figure` renders the
clipped region at high DPI. Phase 0 emits plain raster crops only — no SVG.
"""

from __future__ import annotations

from pathlib import Path

import fitz  # PyMuPDF

from .models.base import LayoutElement
from .preprocess import PageMeta

CROP_DPI = 300


def bbox_to_rect(bbox: tuple[float, float, float, float], scale: float) -> fitz.Rect:
    """Map a pixel-space bbox to a PDF-point rectangle."""
    x1, y1, x2, y2 = bbox
    return fitz.Rect(x1 * scale, y1 * scale, x2 * scale, y2 * scale)


def crop_figure(
    doc: fitz.Document, element: LayoutElement, meta: PageMeta, out_path: Path
) -> Path:
    page = doc[meta.page_index]
    clip = bbox_to_rect(element.bbox, meta.scale)
    pix = page.get_pixmap(clip=clip, dpi=CROP_DPI)
    out_path.parent.mkdir(parents=True, exist_ok=True)
    pix.save(out_path)
    return out_path
