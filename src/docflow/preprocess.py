"""PyMuPDF preprocessing: render document pages to images and capture geometry.

Works for any format PyMuPDF can open — PDF, XPS, EPUB, MOBI, FB2, CBZ, and image
files — since everything downstream operates on rendered page images. This is the
only place we rasterize pages. The resulting :class:`PageImage` objects are what a
:class:`~docflow.models.base.LayoutModel` sees; the :class:`PageMeta` objects carry
the pixel->point scale that figure cropping needs to map a model's pixel bbox back
onto the source page.
"""

from __future__ import annotations

from dataclasses import dataclass

import fitz  # PyMuPDF
from PIL import Image

DEFAULT_DPI = 150


@dataclass
class PageImage:
    page_index: int
    image: Image.Image


@dataclass
class PageMeta:
    page_index: int
    pdf_width_pt: float
    pdf_height_pt: float
    dpi: int

    @property
    def scale(self) -> float:
        """Multiplier to convert image pixels back to PDF points (72 pt/inch)."""
        return 72.0 / self.dpi


def preprocess(
    doc: fitz.Document, dpi: int = DEFAULT_DPI
) -> tuple[list[PageImage], list[PageMeta]]:
    # Reflowable formats (EPUB, MOBI, FB2) carry no intrinsic page size; give them
    # a standard one so pagination and page geometry are well-defined before render.
    if doc.is_reflowable:
        doc.layout(width=612, height=792, fontsize=11)

    pages: list[PageImage] = []
    metas: list[PageMeta] = []
    for i, page in enumerate(doc):
        pix = page.get_pixmap(dpi=dpi)
        mode = "RGBA" if pix.alpha else "RGB"
        img = Image.frombytes(mode, (pix.width, pix.height), pix.samples)
        pages.append(PageImage(page_index=i, image=img))
        rect = page.rect
        metas.append(
            PageMeta(
                page_index=i,
                pdf_width_pt=rect.width,
                pdf_height_pt=rect.height,
                dpi=dpi,
            )
        )
    return pages, metas
