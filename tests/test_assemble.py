import fitz

from docflow.assemble import assemble
from docflow.models.base import Category, LayoutElement, PageLayout
from docflow.preprocess import PageMeta


def _layout():
    # bbox in image pixels at 150 DPI for a 612x792 pt page => 1275x1650 px
    return PageLayout(
        page_index=0,
        image_width=1275,
        image_height=1650,
        elements=[
            LayoutElement(Category.TITLE, (100, 50, 1100, 120), "Doc Title"),
            LayoutElement(Category.SECTION_HEADER, (100, 150, 600, 200), "Section One"),
            LayoutElement(Category.TEXT, (100, 220, 1100, 400), "A paragraph."),
            LayoutElement(Category.LIST_ITEM, (120, 420, 1100, 460), "first item"),
            LayoutElement(Category.FORMULA, (100, 480, 500, 540), r"E = mc^2"),
            LayoutElement(Category.TABLE, (100, 560, 1100, 700), "<table><tr><td>x</td></tr></table>"),
            LayoutElement(Category.CAPTION, (100, 720, 600, 760), "Figure 1"),
            LayoutElement(Category.PAGE_FOOTER, (100, 1600, 1100, 1640), "page 1"),
            LayoutElement(Category.PICTURE, (300, 800, 900, 1200), None),
            LayoutElement(Category.FOOTNOTE, (100, 1500, 1100, 1540), "a footnote"),
        ],
    )


def test_assemble_maps_every_category(tiny_pdf, tmp_path):
    doc = fitz.open(tiny_pdf)
    meta = PageMeta(0, 612, 792, dpi=150)
    body, headings = assemble(doc, [_layout()], [meta], tmp_path)
    doc.close()

    assert "# Doc Title" in body
    assert "## Section One" in body
    assert "A paragraph." in body
    assert "- first item" in body
    assert "$$\nE = mc^2\n$$" in body
    assert "<table>" in body
    assert "*Figure 1*" in body
    assert "page 1" not in body  # page-footer dropped
    assert "[^1]: a footnote" in body  # footnote moved to the end

    # Picture was cropped to a real PNG and referenced.
    assert "![Figure](assets/page0_fig1.png)" in body
    assert (tmp_path / "assets" / "page0_fig1.png").exists()

    assert headings == [(1, "Doc Title"), (2, "Section One")]
