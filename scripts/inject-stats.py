#!/usr/bin/env python3
"""Render stored project stats into the static pages — no client-side JS.

This is the render half of the stats pipeline. `fetch-stats.py` does the
single data grab into data/project-stats.json; this reads that snapshot and
bakes the values into every page at build time. Two modes:

    inject-stats.py --data data/project-stats.json   # render all pages
    inject-stats.py --file gravel.html --set version=v2.2.3 ...   # one page

In render mode the PAGES / AGGREGATE_PAGES maps below decide where each
project's stats land. A project's fields populate matching
<span data-stat="FIELD"> placeholders on its page; the `version` field also
cascades to that page's JSON-LD "softwareVersion" and BibTeX `version = {…}`
(bare semver, a single leading "v" stripped). Shared pages like index.html
pull one field from several projects via project-qualified keys, which do
not cascade.
"""
from __future__ import annotations

import argparse
import json
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent

PLACEHOLDER = re.compile(
    r'(<span data-stat="(?P<key>[a-zA-Z0-9_.-]+)"[^>]*>)(?P<body>[^<]*)(</span>)'
)

# Non-span spots that also carry a version, refreshed by the `version` cascade.
# Each pattern captures (prefix)(value)(suffix).
VERSION_FORMS: dict[str, re.Pattern[str]] = {
    "JSON-LD softwareVersion": re.compile(r'("softwareVersion":\s*")([^"]*)(")'),
    "BibTeX version": re.compile(r"(version = \{)([^}]*)(\})"),
}

# A project's own page: every stored field fills a like-named data-stat span;
# `cascade` also pushes the version into JSON-LD + BibTeX on that page.
PAGES: list[dict] = [
    {"file": "gravel.html", "project": "gravel", "cascade": True},
    {"file": "kindling.html", "project": "kindling", "cascade": True},
    {"file": "wopr.html", "project": "wopr"},
    {"file": "tyche.html", "project": "tyche"},
    {"file": "embeddings.html", "project": "embeddings"},
    {"file": "morass/index.html", "project": "morass", "cascade": True},
]

# Shared pages whose badges pull a single field from several projects.
# file -> { data-stat key : (project, field) }. No cascade.
AGGREGATE_PAGES: dict[str, dict[str, tuple[str, str]]] = {
    "index.html": {
        "gravel-version": ("gravel", "version"),
        "kindling-version": ("kindling", "version"),
        "morass-version": ("morass", "version"),
    },
}


def strip_v(value: str) -> str:
    """Bare semver for JSON-LD / BibTeX: drop a single leading v/V."""
    return value[1:] if value[:1] in ("v", "V") else value


def inject_spans(html: str, replacements: dict[str, str]) -> tuple[str, dict[str, int]]:
    counts: dict[str, int] = {k: 0 for k in replacements}

    def sub(match: re.Match[str]) -> str:
        key = match.group("key")
        if key in replacements:
            counts[key] += 1
            return f"{match.group(1)}{replacements[key]}{match.group(4)}"
        return match.group(0)

    return PLACEHOLDER.sub(sub, html), counts


def cascade_version(html: str, version: str) -> tuple[str, dict[str, int]]:
    bare = strip_v(version)
    counts: dict[str, int] = {}
    for label, pat in VERSION_FORMS.items():
        html, counts[label] = pat.subn(lambda m: f"{m.group(1)}{bare}{m.group(3)}", html)
    return html, counts


def apply_to_file(
    path: Path, spans: dict[str, str], *, cascade: bool, warn_missing: bool
) -> None:
    html = path.read_text(encoding="utf-8")
    new_html, counts = inject_spans(html, spans)

    try:
        rel = path.relative_to(ROOT)
    except ValueError:
        rel = path
    for key, n in counts.items():
        if n:
            print(f"{rel} · {key}: {n}×{spans[key]!r}")
        elif warn_missing:
            print(f"warning: no <span data-stat={key!r}> in {rel}", file=sys.stderr)

    if cascade and "version" in spans:
        new_html, vcounts = cascade_version(new_html, spans["version"])
        bare = strip_v(spans["version"])
        for label, n in vcounts.items():
            if n:
                print(f"{rel} · {label}: {n}×{bare!r}")

    if new_html != html:
        path.write_text(new_html, encoding="utf-8")


def render(store: Path) -> None:
    data: dict[str, dict[str, str]] = json.loads(store.read_text(encoding="utf-8"))

    for page in PAGES:
        proj = data.get(page["project"], {})
        if not proj:
            print(f"warning: no stats for {page['project']!r} in {store.name}", file=sys.stderr)
            continue
        # A page only carries the spans it needs, so don't warn on absent keys.
        apply_to_file(ROOT / page["file"], proj, cascade=page.get("cascade", False),
                      warn_missing=False)

    for file, badges in AGGREGATE_PAGES.items():
        spans = {
            key: data[proj][field]
            for key, (proj, field) in badges.items()
            if proj in data and field in data[proj]
        }
        if spans:
            apply_to_file(ROOT / file, spans, cascade=False, warn_missing=True)


def render_one(file: str, replacements: dict[str, str]) -> None:
    cascade = "version" in replacements
    apply_to_file(Path(file), replacements, cascade=cascade, warn_missing=True)


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("--data", help="stats JSON to render into all mapped pages")
    ap.add_argument("--file", help="single HTML file to edit in place (with --set)")
    ap.add_argument(
        "--set", action="append", default=[], metavar="KEY=VALUE",
        help="data-stat key and value to inject; repeatable (requires --file)",
    )
    args = ap.parse_args()

    if args.data:
        render(Path(args.data))
        return 0

    if not args.file:
        ap.error("provide --data (render store) or --file with --set (single page)")

    replacements: dict[str, str] = {}
    for pair in args.set:
        if "=" not in pair:
            sys.exit(f"--set expects KEY=VALUE, got: {pair!r}")
        key, value = pair.split("=", 1)
        replacements[key] = value
    render_one(args.file, replacements)
    return 0


if __name__ == "__main__":
    sys.exit(main())
