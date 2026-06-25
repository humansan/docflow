import zipfile

from PIL import Image

from docflow import convert


def test_convert_mock_end_to_end(tiny_pdf, tmp_path):
    out = tmp_path / "out"
    result = convert(tiny_pdf, model="mock", out_dir=out)

    assert result.markdown_path.exists()
    assert result.markdown_path == out / "result.md"

    md = result.markdown_path.read_text(encoding="utf-8")
    assert "# Table of Contents" in md
    assert "# Sample Page 1" in md  # mock title
    assert "![Figure](assets/page0_fig1.png)" in md

    # The mock places a Picture box, so a crop should have been written.
    assert (out / "assets" / "page0_fig1.png").exists()


def test_convert_accepts_image(tmp_path):
    """A bare image opens as a 1-page MuPDF document — the engine handles it."""
    img_path = tmp_path / "scan.png"
    Image.new("RGB", (800, 1000), "white").save(img_path)

    result = convert(img_path, model="mock", out_dir=tmp_path / "out")

    assert result.markdown_path.exists()
    assert "# Sample Page 1" in result.markdown_path.read_text(encoding="utf-8")
    assert (tmp_path / "out" / "assets" / "page0_fig1.png").exists()


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
