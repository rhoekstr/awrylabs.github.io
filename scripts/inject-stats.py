#!/usr/bin/env python3
"""Inject values into <span data-stat="KEY">…</span> placeholders.

Used by .github/workflows/refresh-gravel-stats.yml to keep gravel.html's
hero badge and footer current with the public rhoekstr/gravel repo
without shipping any client-side JavaScript. Every replacement happens
at build time; the deployed page is static HTML.

Usage:
    inject-stats.py --file gravel.html \\
        --set version=v2.1 \\
        --set released="April 2026" \\
        --set last-commit=2026-04-14
"""
from __future__ import annotations

import argparse
import re
import sys


PLACEHOLDER = re.compile(
    r'(<span data-stat="(?P<key>[a-zA-Z0-9_-]+)"[^>]*>)(?P<body>[^<]*)(</span>)'
)


def inject(html: str, replacements: dict[str, str]) -> tuple[str, dict[str, int]]:
    counts: dict[str, int] = {k: 0 for k in replacements}

    def sub(match: re.Match[str]) -> str:
        key = match.group("key")
        if key in replacements:
            counts[key] += 1
            return f"{match.group(1)}{replacements[key]}{match.group(4)}"
        return match.group(0)

    return PLACEHOLDER.sub(sub, html), counts


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("--file", required=True, help="HTML file to edit in place")
    ap.add_argument(
        "--set",
        action="append",
        default=[],
        metavar="KEY=VALUE",
        help="data-stat key and value to inject; repeatable",
    )
    args = ap.parse_args()

    replacements: dict[str, str] = {}
    for pair in args.set:
        if "=" not in pair:
            sys.exit(f"--set expects KEY=VALUE, got: {pair!r}")
        key, value = pair.split("=", 1)
        replacements[key] = value

    with open(args.file, encoding="utf-8") as f:
        html = f.read()

    new_html, counts = inject(html, replacements)

    for key, n in counts.items():
        if n == 0:
            print(
                f"warning: no <span data-stat={key!r}> placeholders found in {args.file}",
                file=sys.stderr,
            )
        else:
            print(f"{key}: replaced {n} occurrence(s) with {replacements[key]!r}")

    if new_html != html:
        with open(args.file, "w", encoding="utf-8") as f:
            f.write(new_html)

    return 0


if __name__ == "__main__":
    sys.exit(main())
