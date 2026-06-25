"""Offline placeholder model — no GPU, no network.

Emits a plausible layout sized to each page image (boxes as fractions of the
real pixel dimensions) so the entire pipeline — assembly, TOC, and figure
cropping — runs end-to-end on any PDF. The text is filler; the point is to
exercise the plumbing, not to read the document.
"""

from __future__ import annotations

from ..preprocess import PageImage
from .base import Category, LayoutElement, PageLayout


class MockLayoutModel:
    def parse(self, pages: list[PageImage]) -> list[PageLayout]:
        layouts: list[PageLayout] = []
        for p in pages:
            w, h = p.image.size
            elements = [
                LayoutElement(
                    Category.TITLE,
                    (0.10 * w, 0.05 * h, 0.90 * w, 0.12 * h),
                    f"Sample Page {p.page_index + 1}",
                ),
                LayoutElement(
                    Category.SECTION_HEADER,
                    (0.10 * w, 0.15 * h, 0.60 * w, 0.20 * h),
                    "A Section",
                ),
                LayoutElement(
                    Category.TEXT,
                    (0.10 * w, 0.22 * h, 0.90 * w, 0.40 * h),
                    "Placeholder paragraph produced by the mock layout model.",
                ),
                LayoutElement(
                    Category.PICTURE,
                    (0.25 * w, 0.45 * h, 0.75 * w, 0.75 * h),
                    None,
                ),
                LayoutElement(
                    Category.FORMULA,
                    (0.10 * w, 0.80 * h, 0.50 * w, 0.86 * h),
                    r"E = mc^2",
                ),
            ]
            layouts.append(PageLayout(p.page_index, w, h, elements))
        return layouts
