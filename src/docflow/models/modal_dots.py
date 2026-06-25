"""Adapter that runs dots.mocr inference on Modal — Phase 1's production GPU boundary.

Mirrors :class:`~docflow.models.remote_dots.RemoteDotsModel`, but invokes the deployed
Modal function via the SDK (``.remote()``) instead of HTTP. All pages of a document are
sent in a single call, so a document incurs at most one cold start. The Modal app lives
in ``modal_app.py`` at the repo root (deploy with ``modal deploy modal_app.py``).
"""

from __future__ import annotations

import io

from ..preprocess import PageImage
from .base import PageLayout

APP_NAME = "docflow-ocr"
CLS_NAME = "DotsOCR"


def _png_bytes(image) -> bytes:
    buf = io.BytesIO()
    image.save(buf, format="PNG")
    return buf.getvalue()


class ModalDotsModel:
    def __init__(self, app_name: str = APP_NAME, cls_name: str = CLS_NAME):
        import modal  # imported lazily so the package doesn't hard-require Modal

        self._cls = modal.Cls.from_name(app_name, cls_name)

    def parse(self, pages: list[PageImage]) -> list[PageLayout]:
        payload = [
            {"page_index": p.page_index, "png": _png_bytes(p.image)} for p in pages
        ]
        raw = self._cls().parse.remote(payload)  # one call, all pages
        return [PageLayout.from_dict(d) for d in raw]
