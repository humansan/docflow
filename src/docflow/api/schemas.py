"""Pydantic models describing the HTTP contract.

These shape the auto-generated OpenAPI schema, which we start treating as the
first draft of the public API contract (planning principle #5) even though the
path is unversioned in this scaffold phase.
"""

from __future__ import annotations

from pydantic import BaseModel, ConfigDict, Field


class ConvertResponse(BaseModel):
    # A field literally named ``model`` collides with Pydantic's protected
    # ``model_`` namespace; opt out so it stays a plain field, not a warning.
    model_config = ConfigDict(protected_namespaces=())

    filename: str = Field(description="Original uploaded filename.")
    model: str = Field(description="Layout model used for this conversion.")
    dpi: int = Field(description="Render DPI used for this conversion.")
    markdown: str = Field(description="The converted Markdown.")
    assets: list[str] = Field(
        default_factory=list,
        description="Figure-crop filenames referenced by the Markdown; [] if none.",
    )


class ErrorResponse(BaseModel):
    detail: str
