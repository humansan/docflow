"""Adapter for a remote dots.mocr inference server (Colab during Phase 0).

Posts each rendered page image to the server's ``/parse`` endpoint and
deserializes the dots.ocr-shaped JSON back into :class:`PageLayout`. The server
URL comes from ``DOCFLOW_DOTS_URL`` (the tunnel printed by the Colab notebook).
This whole class is replaced by a Modal call in Phase 1 without touching the
rest of the pipeline.
"""

from __future__ import annotations

import io
import os

import requests

from ..preprocess import PageImage
from .base import PageLayout

DEFAULT_TIMEOUT = 300  # seconds; cold GPU + a multi-page PDF can be slow


class RemoteDotsModel:
    def __init__(self, base_url: str | None = None, timeout: int = DEFAULT_TIMEOUT):
        self.base_url = (base_url or os.environ.get("DOCFLOW_DOTS_URL", "")).rstrip("/")
        if not self.base_url:
            raise RuntimeError(
                "Set DOCFLOW_DOTS_URL to the dots.mocr server URL "
                "(run notebooks/dots_server.ipynb and copy the printed tunnel URL)."
            )
        self.timeout = timeout

    def parse(self, pages: list[PageImage]) -> list[PageLayout]:
        results: list[PageLayout] = []
        for p in pages:
            buf = io.BytesIO()
            p.image.save(buf, format="PNG")
            buf.seek(0)
            resp = requests.post(
                f"{self.base_url}/parse",
                files={"image": (f"page_{p.page_index}.png", buf, "image/png")},
                data={"page_index": str(p.page_index)},
                timeout=self.timeout,
            )
            if not resp.ok:
                # Surface the server-side error/traceback instead of a bare status.
                detail = resp.text
                try:
                    payload = resp.json()
                    detail = payload.get("traceback") or payload.get("error") or detail
                except ValueError:
                    pass
                raise RuntimeError(
                    f"dots server returned {resp.status_code} for page "
                    f"{p.page_index}:\n{detail}"
                )
            results.append(PageLayout.from_dict(resp.json()))
        return results
