"""Layout model registry. ``get_model`` resolves a name to an implementation."""

from __future__ import annotations

from .base import Category, LayoutElement, LayoutModel, PageLayout

__all__ = ["Category", "LayoutElement", "LayoutModel", "PageLayout", "get_model"]


def get_model(name: str) -> LayoutModel:
    if name == "mock":
        from .mock import MockLayoutModel

        return MockLayoutModel()
    if name == "dots":
        from .remote_dots import RemoteDotsModel

        return RemoteDotsModel()
    raise ValueError(f"Unknown model {name!r} (expected 'mock' or 'dots')")
