"""FastAPI application factory and ASGI entry point.

Run locally with::

    uv run uvicorn docflow.api.app:app --reload
"""

from __future__ import annotations

from fastapi import FastAPI

from .routes import router


def create_app() -> FastAPI:
    app = FastAPI(
        title="Docflow API",
        version="0.0.0",  # scaffold; the /v1 contract starts in Phase 3
        description=(
            "Synchronous PDF→Markdown conversion "
            "(scaffold — the async API lands in Phase 3)."
        ),
    )
    app.include_router(router)
    return app


app = create_app()  # uvicorn target: docflow.api.app:app
