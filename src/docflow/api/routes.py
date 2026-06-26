"""HTTP routes: a liveness probe and the synchronous convert endpoint.

The convert handler is a plain ``def`` (not ``async def``) on purpose: ``convert()``
is CPU-bound and blocks on the Modal call, so Starlette runs it in its threadpool and
one slow conversion can't stall the event loop / other requests.
"""

from __future__ import annotations

import io
import shutil
import zipfile
from pathlib import Path
from typing import Literal

from fastapi import APIRouter, File, Form, Header, HTTPException, Query, UploadFile
from fastapi.responses import JSONResponse, PlainTextResponse, StreamingResponse
from starlette.background import BackgroundTask

from .runner import UnsupportedFormatError, run_conversion
from .schemas import ConvertResponse, ErrorResponse
from .settings import settings

router = APIRouter()


@router.get("/health", tags=["meta"], summary="Liveness probe")
def health() -> dict[str, str]:
    """Cheap health check — does not touch the engine."""
    return {"status": "ok"}


def _wants_json(response: str, accept: str | None) -> bool:
    return response == "json" or (accept is not None and "application/json" in accept)


def _build_zip(markdown: str, assets_dir: Path) -> io.BytesIO:
    """In-memory zip of ``result.md`` + the ``*_assets/`` folder.

    The Markdown's figure links are relative (``<stem>_assets/pageN_figM.png``), so
    keeping the assets folder under its original name makes those links resolve once
    the archive is unpacked.
    """
    buf = io.BytesIO()
    with zipfile.ZipFile(buf, "w", zipfile.ZIP_DEFLATED) as zf:
        zf.writestr("result.md", markdown)
        if assets_dir.exists():
            for f in sorted(assets_dir.rglob("*")):
                if f.is_file():
                    arc = Path(assets_dir.name) / f.relative_to(assets_dir)
                    zf.write(f, arc.as_posix())
    buf.seek(0)
    return buf


@router.post(
    "/convert",
    tags=["conversion"],
    summary="Convert a document to Markdown (synchronous)",
    responses={
        200: {"model": ConvertResponse, "description": "Markdown, JSON, or a zip bundle."},
        400: {"model": ErrorResponse, "description": "Empty upload."},
        413: {"model": ErrorResponse, "description": "Upload exceeds the size limit."},
        415: {"model": ErrorResponse, "description": "Unsupported file type."},
        500: {"model": ErrorResponse, "description": "Conversion failed."},
    },
)
def convert_document(
    file: UploadFile = File(..., description="The document to convert."),
    model: str = Form(default=settings.default_model, description="Layout model."),
    dpi: int = Form(default=settings.default_dpi, description="Render DPI."),
    bundle: Literal["none", "zip"] = Query(
        "none", description="`zip` returns result.md + figure crops as an archive."
    ),
    response: Literal["markdown", "json"] = Query(
        "markdown", description="`json` returns a structured ConvertResponse."
    ),
    accept: str | None = Header(default=None),
):
    data = file.file.read()
    if not data:
        raise HTTPException(status_code=400, detail="Empty upload.")
    if len(data) > settings.max_upload_bytes:
        raise HTTPException(
            status_code=413,
            detail=f"Upload exceeds the {settings.max_upload_bytes}-byte limit.",
        )

    try:
        result, tmp = run_conversion(
            file.filename or "upload", data, model=model, dpi=dpi
        )
    except UnsupportedFormatError as exc:
        raise HTTPException(status_code=415, detail=str(exc)) from exc
    except Exception as exc:  # engine failure -> 500
        raise HTTPException(status_code=500, detail=f"Conversion failed: {exc}") from exc

    cleanup = BackgroundTask(shutil.rmtree, tmp, ignore_errors=True)

    if bundle == "zip":
        # Temp dir must outlive the stream, so clean up only in the background task.
        buf = _build_zip(result.markdown, result.assets_dir)
        headers = {"Content-Disposition": f'attachment; filename="{Path(file.filename or "result").stem}.zip"'}
        return StreamingResponse(
            buf, media_type="application/zip", headers=headers, background=cleanup
        )

    # Non-zip paths: Markdown and asset names are already in memory; the temp dir
    # is still removed via the background task for uniformity.
    assets = (
        sorted(p.name for p in result.assets_dir.iterdir() if p.is_file())
        if result.assets_dir.exists()
        else []
    )

    if _wants_json(response, accept):
        payload = ConvertResponse(
            filename=file.filename or "upload",
            model=model,
            dpi=dpi,
            markdown=result.markdown,
            assets=assets,
        )
        return JSONResponse(content=payload.model_dump(), background=cleanup)

    return PlainTextResponse(
        result.markdown, media_type="text/markdown", background=cleanup
    )
