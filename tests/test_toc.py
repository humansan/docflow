from docflow.toc import build_toc, slugify


def test_slugify_basic():
    assert slugify("Chapter 1: Intro!") == "chapter-1-intro"


def test_slugify_collapses_whitespace():
    assert slugify("  Multiple   Spaces  ") == "multiple-spaces"


def test_build_toc_nesting_and_anchors():
    toc = build_toc([(1, "Calculus"), (2, "Limits"), (1, "Algebra")])
    lines = toc.splitlines()
    assert lines[0] == "# Table of Contents"
    assert "- [Calculus](#calculus)" in toc
    assert "  - [Limits](#limits)" in toc  # level 2 indented two spaces
    assert "- [Algebra](#algebra)" in toc
