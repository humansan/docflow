"""The internal layout contract shared by every model implementation.

Deliberately mirrors dots.ocr's output schema so the mock, the remote dots.mocr
adapter, and a future Modal adapter are all drop-in replacements: ``bbox`` is
``[x1, y1, x2, y2]`` in **image pixels**, ``category`` is one of dots.ocr's 11
layout types, and ``text`` carries Markdown (LaTeX for Formula, HTML for Table,
``None`` for Picture). Elements arrive in reading order.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum
from typing import TYPE_CHECKING, Any, Protocol, runtime_checkable

if TYPE_CHECKING:
    from ..preprocess import PageImage


class Category(str, Enum):
    """The 11 layout element types emitted by dots.ocr."""

    TITLE = "Title"
    SECTION_HEADER = "Section-header"
    TEXT = "Text"
    LIST_ITEM = "List-item"
    FORMULA = "Formula"
    TABLE = "Table"
    PICTURE = "Picture"
    CAPTION = "Caption"
    FOOTNOTE = "Footnote"
    PAGE_HEADER = "Page-header"
    PAGE_FOOTER = "Page-footer"


@dataclass
class LayoutElement:
    category: Category
    bbox: tuple[float, float, float, float]  # [x1, y1, x2, y2] in image pixels
    text: str | None = None  # None for Picture; LaTeX for Formula; HTML for Table

    @classmethod
    def from_dict(cls, d: dict[str, Any]) -> "LayoutElement":
        x1, y1, x2, y2 = d["bbox"]
        return cls(
            category=Category(d["category"]),
            bbox=(float(x1), float(y1), float(x2), float(y2)),
            text=d.get("text"),
        )


@dataclass
class PageLayout:
    page_index: int
    image_width: int
    image_height: int
    elements: list[LayoutElement] = field(default_factory=list)

    @classmethod
    def from_dict(cls, d: dict[str, Any]) -> "PageLayout":
        return cls(
            page_index=int(d["page_index"]),
            image_width=int(d["image_width"]),
            image_height=int(d["image_height"]),
            elements=[LayoutElement.from_dict(e) for e in d.get("elements", [])],
        )


@runtime_checkable
class LayoutModel(Protocol):
    """Anything that turns rendered page images into layout JSON."""

    def parse(self, pages: "list[PageImage]") -> list[PageLayout]:
        ...
