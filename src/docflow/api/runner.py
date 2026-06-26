"""Bridge between an HTTP upload (bytes in memory) and the file-oriented engine.

No FastAPI types live here, so this stays unit-testable on its own. The caller
owns the returned temp directory and must delete it *after* the response is sent
(see the zip/streaming note in ``routes.py``).
"""

from __future__ import annotations

import tempfile
from pathlib import Path

from ..convert import SUPPORTED_SUFFIXES, ConversionResult, convert


class UnsupportedFormatError(Exception):
    """The upload's suffix isn't something PyMuPDF can open."""

    def __init__(self, suffix: str) -> None:
        self.suffix = suffix
        super().__init__(
            f"Unsupported file type {suffix!r}; "
            f"expected one of {sorted(SUPPORTED_SUFFIXES)}"
        )


def run_conversion(
    filename: str, data: bytes, *, model: str, dpi: int
) -> tuple[ConversionResult, Path]:
    """Write ``data`` to a temp file named ``filename`` and convert it.

    Returns the :class:`ConversionResult` and the temp directory root, which the
    caller is responsible for cleaning up once the response has been delivered.
    """
    name = Path(filename).name
    suffix = Path(name).suffix.lower()
    if suffix not in SUPPORTED_SUFFIXES:
        raise UnsupportedFormatError(suffix)

    tmp = Path(tempfile.mkdtemp(prefix="docflow_"))
    src = tmp / name  # preserve suffix so PyMuPDF picks the right opener
    src.write_bytes(data)
    result = convert(src, model=model, dpi=dpi, out_dir=tmp / "out")
    return result, tmp
