import shutil
import zipfile

from PIL import Image

from docflow import convert, convert_path


def test_convert_mock_end_to_end(tiny_pdf, tmp_path):
    out = tmp_path / "out"
    result = convert(tiny_pdf, model="mock", out_dir=out)

    assert result.markdown_path.exists()
    assert result.markdown_path == out / "tiny_out.md"  # named after the source

    md = result.markdown_path.read_text(encoding="utf-8")
    assert "# Table of Contents" in md
    assert "# Sample Page 1" in md  # mock title
    assert "![Figure](tiny_assets/page0_fig1.png)" in md

    # The mock places a Picture box, so a crop should have been written.
    assert (out / "tiny_assets" / "page0_fig1.png").exists()


def test_convert_accepts_image(tmp_path):
    """A bare image opens as a 1-page MuPDF document — the engine handles it."""
    img_path = tmp_path / "scan.png"
    Image.new("RGB", (800, 1000), "white").save(img_path)

    result = convert(img_path, model="mock", out_dir=tmp_path / "out")

    assert result.markdown_path == tmp_path / "out" / "scan_out.md"
    assert "# Sample Page 1" in result.markdown_path.read_text(encoding="utf-8")
    assert (tmp_path / "out" / "scan_assets" / "page0_fig1.png").exists()


def test_convert_accepts_cbz(tmp_path):
    """CBZ (a zip of page images) uses a different MuPDF handler than PDF."""
    pages = []
    for n in range(2):
        p = tmp_path / f"p{n}.png"
        Image.new("RGB", (800, 1000), "white").save(p)
        pages.append(p)
    cbz = tmp_path / "comic.cbz"
    with zipfile.ZipFile(cbz, "w") as z:
        for p in pages:
            z.write(p, p.name)

    result = convert(cbz, model="mock", out_dir=tmp_path / "out2")

    md = result.markdown_path.read_text(encoding="utf-8")
    assert "# Sample Page 1" in md
    assert "# Sample Page 2" in md  # both pages processed


def test_convert_path_iterates_folder(tiny_pdf, tmp_path):
    """A folder input converts every supported document and skips the rest."""
    folder = tmp_path / "docs"
    folder.mkdir()
    shutil.copy(tiny_pdf, folder / "a.pdf")
    Image.new("RGB", (800, 1000), "white").save(folder / "b.png")
    (folder / "notes.txt").write_text("not a document")  # must be ignored

    out = tmp_path / "out"
    results = list(convert_path(folder, model="mock", out_dir=out))

    assert len(results) == 2  # .txt skipped
    assert sorted(r.markdown_path.name for r in results) == ["a_out.md", "b_out.md"]
    assert (out / "a_out.md").exists()
    assert (out / "b_out.md").exists()
    # Per-document asset folders don't collide.
    assert (out / "a_assets" / "page0_fig1.png").exists()
    assert (out / "b_assets" / "page0_fig1.png").exists()


def test_convert_path_single_file_returns_one(tiny_pdf, tmp_path):
    results = list(convert_path(tiny_pdf, model="mock", out_dir=tmp_path / "out"))
    assert len(results) == 1
    assert results[0].markdown_path.name == "tiny_out.md"
