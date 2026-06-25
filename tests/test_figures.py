import fitz

from docflow.figures import bbox_to_rect
from docflow.preprocess import PageMeta


def test_scale_is_points_per_pixel():
    assert PageMeta(0, 612, 792, dpi=150).scale == 72.0 / 150.0


def test_bbox_to_rect_maps_pixels_to_points():
    # At 150 DPI, 1275 px wide maps back to 612 pt (612 * 150 / 72 == 1275).
    scale = PageMeta(0, 612, 792, dpi=150).scale
    rect = bbox_to_rect((0, 0, 1275, 1650), scale)
    assert rect == fitz.Rect(0, 0, 612, 792)
