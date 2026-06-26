"""HTTP layer for Docflow — a thin FastAPI shell around the engine.

A leaf package: it imports the engine (``docflow.convert``) and nothing in the
engine imports it back, mirroring the one-directional ``LayoutModel`` seam.
"""

from __future__ import annotations

from .app import app, create_app

__all__ = ["app", "create_app"]
