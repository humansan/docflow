"""Command-line entry point: ``docflow convert <pdf> [...]``."""

from __future__ import annotations

import argparse
import sys

from .convert import convert
from .preprocess import DEFAULT_DPI


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(prog="docflow")
    sub = parser.add_subparsers(dest="command", required=True)

    c = sub.add_parser("convert", help="Convert a document to Markdown")
    c.add_argument(
        "source",
        help="Path to the input document (PDF, XPS, EPUB, MOBI, FB2, CBZ, or image)",
    )
    c.add_argument("-o", "--out-dir", default="out", help="Output directory (default: out)")
    c.add_argument(
        "--model",
        default="mock",
        choices=["mock", "dots"],
        help="Layout model: 'mock' (offline) or 'dots' (remote dots.mocr server)",
    )
    c.add_argument("--dpi", type=int, default=DEFAULT_DPI, help=f"Render DPI (default: {DEFAULT_DPI})")

    args = parser.parse_args(argv)

    if args.command == "convert":
        result = convert(args.source, model=args.model, dpi=args.dpi, out_dir=args.out_dir)
        print(f"Wrote {result.markdown_path}")
        print(f"Assets in {result.assets_dir}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
