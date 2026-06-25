"""Table-of-contents generation from collected headings.

Ports the slugify + TOC-builder approach from ``.docs/DOCUMENT_PLANNING.md``.
Markdown viewers turn ``#``/``##`` headings into anchors; we mirror that
anchoring here so the generated TOC links actually jump.
"""

from __future__ import annotations

import re


def slugify(text: str) -> str:
    """Convert a heading into a GitHub-style Markdown anchor."""
    text = text.lower().strip()
    text = re.sub(r"[^\w\s-]", "", text)
    return re.sub(r"\s+", "-", text)


def build_toc(headings: list[tuple[int, str]]) -> str:
    """Build a nested, clickable TOC from ``(level, text)`` pairs."""
    lines = ["# Table of Contents", ""]
    for level, text in headings:
        indent = "  " * (level - 1)
        lines.append(f"{indent}- [{text}](#{slugify(text)})")
    return "\n".join(lines)
