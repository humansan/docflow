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
