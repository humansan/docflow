"""Env-driven configuration for the HTTP layer.

Dependency-light: plain ``os.environ`` reads wrapped in a small dataclass. A single
module-level :data:`settings` instance is imported by the routes; tests monkeypatch
its attributes (e.g. ``max_upload_bytes``) to exercise the size guards.
"""

from __future__ import annotations

import os
from dataclasses import dataclass

from ..preprocess import DEFAULT_DPI

_DEFAULT_MAX_UPLOAD_BYTES = 50 * 1024 * 1024  # 50 MiB


@dataclass
class Settings:
    default_model: str
    default_dpi: int
    max_upload_bytes: int


def get_settings() -> Settings:
    return Settings(
        default_model=os.environ.get("DOCFLOW_DEFAULT_MODEL", "modal"),
        default_dpi=int(os.environ.get("DOCFLOW_DEFAULT_DPI", DEFAULT_DPI)),
        max_upload_bytes=int(
            os.environ.get("DOCFLOW_MAX_UPLOAD_BYTES", _DEFAULT_MAX_UPLOAD_BYTES)
        ),
    )


settings = get_settings()
