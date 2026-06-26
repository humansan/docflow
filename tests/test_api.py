"""HTTP-layer tests via FastAPI's TestClient. All use ``model=mock`` — no GPU."""

from __future__ import annotations

import io
import tempfile
import zipfile
from pathlib import Path

import pytest
from fastapi.testclient import TestClient

from docflow.api.app import create_app
from docflow.api.settings import settings


@pytest.fixture
def client():
    return TestClient(create_app())


def _upload(path: Path, name: str = "tiny.pdf"):
    return {"file": (name, path.read_bytes(), "application/pdf")}


def _docflow_tmp_count() -> int:
    return len(list(Path(tempfile.gettempdir()).glob("docflow_*")))


def test_health(client):
    r = client.get("/health")
    assert r.status_code == 200
    assert r.json() == {"status": "ok"}


def test_convert_markdown(client, tiny_pdf):
    before = _docflow_tmp_count()
    r = client.post("/convert", files=_upload(tiny_pdf), data={"model": "mock"})

    assert r.status_code == 200
    assert r.headers["content-type"].startswith("text/markdown")
    assert "# Table of Contents" in r.text
    assert "# Sample Page 1" in r.text
    # Temp dir cleaned up by the background task once the response is delivered.
    assert _docflow_tmp_count() == before


def test_convert_json(client, tiny_pdf):
    r = client.post(
        "/convert?response=json", files=_upload(tiny_pdf), data={"model": "mock"}
    )

    assert r.status_code == 200
    body = r.json()
    assert body["filename"] == "tiny.pdf"
    assert body["model"] == "mock"
    assert "# Sample Page 1" in body["markdown"]
    assert "page0_fig1.png" in body["assets"]


def test_convert_zip(client, tiny_pdf):
    before = _docflow_tmp_count()
    r = client.post(
        "/convert?bundle=zip", files=_upload(tiny_pdf), data={"model": "mock"}
    )

    assert r.status_code == 200
    assert r.headers["content-type"] == "application/zip"
    with zipfile.ZipFile(io.BytesIO(r.content)) as zf:
        names = zf.namelist()
    assert "result.md" in names
    assert "tiny_assets/page0_fig1.png" in names
    assert _docflow_tmp_count() == before


def test_unsupported_type_415(client):
    r = client.post(
        "/convert",
        files={"file": ("notes.txt", b"not a document", "text/plain")},
        data={"model": "mock"},
    )
    assert r.status_code == 415


def test_empty_upload_400(client):
    r = client.post(
        "/convert",
        files={"file": ("empty.pdf", b"", "application/pdf")},
        data={"model": "mock"},
    )
    assert r.status_code == 400


def test_oversized_upload_413(client, tiny_pdf, monkeypatch):
    monkeypatch.setattr(settings, "max_upload_bytes", 10)
    r = client.post("/convert", files=_upload(tiny_pdf), data={"model": "mock"})
    assert r.status_code == 413
