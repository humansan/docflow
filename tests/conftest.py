from __future__ import annotations

import fitz  # PyMuPDF
import pytest


@pytest.fixture
def tiny_pdf(tmp_path):
    """A minimal one-page PDF (US Letter, 612x792 pt) with a little text."""
    doc = fitz.open()
    page = doc.new_page(width=612, height=792)
    page.insert_text((72, 72), "Hello Docflow", fontsize=24)
    page.insert_text((72, 200), "Body text here.", fontsize=12)
    path = tmp_path / "tiny.pdf"
    doc.save(path)
    doc.close()
    return path
