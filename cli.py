"""
CLI for Trust-Aware Web Audit Tool.

Usage:
  python cli.py <url> [--max-pages N] [--output report.html]
  python cli.py https://example.com --max-pages 10
"""

import argparse
import sys
from pathlib import Path

# Ensure project root is on path when run as script
sys.path.insert(0, str(Path(__file__).resolve().parent))

from app import run_audit
from report import generate_html_report


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Trust-Aware Web Audit Tool — crawl a site and generate an HTML report."
    )
    parser.add_argument("url", help="Target URL to audit (e.g. https://example.com)")
    parser.add_argument(
        "--max-pages",
        type=int,
        default=None,
        metavar="N",
        help="Max pages to crawl (default: 50)",
    )
    parser.add_argument(
        "--output",
        "-o",
        type=Path,
        default=None,
        help="Write HTML report to this file (default: print to stdout)",
    )
    args = parser.parse_args()

    try:
        report = run_audit(args.url, max_pages=args.max_pages)
    except Exception as e:
        detail = getattr(e, "detail", str(e))
        if isinstance(detail, list):
            detail = "; ".join(str(x) for x in detail)
        print(f"Audit failed: {detail}", file=sys.stderr)
        return 1

    html = generate_html_report(report)
    if args.output:
        args.output.write_text(html, encoding="utf-8")
        print(f"Report written to {args.output}", file=sys.stderr)
    else:
        print(html)
    return 0


if __name__ == "__main__":
    sys.exit(main())
