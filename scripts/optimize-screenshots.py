#!/usr/bin/env python3
"""Downscale Morass app screenshots for the web.

The captured screenshots are full device resolution (~1179px wide) but on
the /morass/ pages they never render wider than ~300px. Serving the full
files wastes bandwidth, so this script downscales them to a width that is
still crisp on retina (2x/3x) at the sizes we display.

Originals live in the marketing repo (mire/marketing/screenshots), so the
in-place downscale here is safe and reversible. Idempotent: images already
at or below the target width are left untouched, so it's safe to re-run
after dropping in freshly captured screenshots.

Usage:
    python3 scripts/optimize-screenshots.py
"""
from __future__ import annotations

import glob
import os
from pathlib import Path

from PIL import Image

TARGET_W = 760
SHOTS = Path(__file__).parent.parent / "morass" / "screenshots"


def main() -> int:
    before = after = 0
    for path in sorted(glob.glob(str(SHOTS / "*.png"))):
        size_before = os.path.getsize(path)
        before += size_before
        im = Image.open(path)
        if im.width <= TARGET_W:
            after += size_before
            print(f"skip  {os.path.basename(path):20} {im.width}px (already ≤{TARGET_W})")
            continue
        h = round(im.height * TARGET_W / im.width)
        im = im.convert("RGB").resize((TARGET_W, h), Image.LANCZOS)
        im.save(path, "PNG", optimize=True)
        size_after = os.path.getsize(path)
        after += size_after
        print(
            f"scale {os.path.basename(path):20} → {TARGET_W}x{h}  "
            f"{size_before/1024:7.1f} → {size_after/1024:6.1f} KB"
        )

    saved = before - after
    print(
        f"\nTotal: {before/1024/1024:.2f} MB → {after/1024/1024:.2f} MB "
        f"(saved {saved/1024/1024:.2f} MB, {saved/before*100:.0f}%)"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
