"""Command-line entry point: ``docflow convert <pdf> [...]``."""

from __future__ import annotations

import argparse
import sys

from .convert import convert_path
from .preprocess import DEFAULT_DPI


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(prog="docflow")
    sub = parser.add_subparsers(dest="command", required=True)

    c = sub.add_parser("convert", help="Convert a document to Markdown")
    c.add_argument(
        "source",
        help="A document or a folder of documents (PDF, XPS, EPUB, MOBI, FB2, CBZ, or image)",
    )
    c.add_argument("-o", "--out-dir", default="out", help="Output directory (default: out)")
    c.add_argument(
        "--model",
        default="mock",
        choices=["mock", "dots", "modal"],
        help="Layout model: 'mock' (offline), 'dots' (Colab dots.mocr server), "
        "or 'modal' (deployed Modal GPU function)",
    )
    c.add_argument("--dpi", type=int, default=DEFAULT_DPI, help=f"Render DPI (default: {DEFAULT_DPI})")

    args = parser.parse_args(argv)

    if args.command == "convert":
        results = convert_path(
            args.source, model=args.model, dpi=args.dpi, out_dir=args.out_dir
        )
        for r in results:
            print(f"Wrote {r.markdown_path}")
        if len(results) > 1:
            print(f"Converted {len(results)} documents to {args.out_dir}/")
    return 0


if __name__ == "__main__":
    sys.exit(main())
