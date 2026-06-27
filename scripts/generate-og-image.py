#!/usr/bin/env python3
"""Generate the OpenGraph / Twitter card image (1200×630 PNG).

Output: assets/og-image.png

Run manually whenever the wordmark / tagline / project list changes:

    python3 scripts/generate-og-image.py

Why a script and not a static asset: branding may evolve, project list
will grow, and re-running this is cheaper than booting a design tool.
"""
from __future__ import annotations

from pathlib import Path

from PIL import Image, ImageDraw, ImageFont

W, H = 1200, 630

OUT = Path(__file__).parent.parent / "assets" / "og-image.png"

# macOS system fonts. Falls back to PIL's default if the explicit paths
# don't exist (the script is run on a developer machine, not in CI).
FONT_CANDIDATES = {
    "italic": [
        "/System/Library/Fonts/Supplemental/Georgia Italic.ttf",
        "/System/Library/Fonts/Supplemental/Times New Roman Italic.ttf",
        "/Library/Fonts/Georgia Italic.ttf",
    ],
    "bold": [
        "/System/Library/Fonts/Supplemental/Georgia Bold.ttf",
        "/System/Library/Fonts/Supplemental/Arial Bold.ttf",
    ],
    "regular": [
        "/System/Library/Fonts/Helvetica.ttc",
        "/System/Library/Fonts/Supplemental/Arial.ttf",
    ],
}


def load_font(kind: str, size: int) -> ImageFont.FreeTypeFont:
    for path in FONT_CANDIDATES[kind]:
        if Path(path).exists():
            try:
                return ImageFont.truetype(path, size)
            except OSError:
                continue
    return ImageFont.load_default()


def main() -> None:
    img = Image.new("RGB", (W, H), "#0a0a0c")
    draw = ImageDraw.Draw(img)

    # Wordmark
    italic = load_font("italic", 96)
    bold = load_font("bold", 96)

    # Position wordmark; measure each word so the spacing is exact
    margin_x = 100
    wordmark_y = 120
    awry_w = draw.textlength("awry", font=italic)
    draw.text((margin_x, wordmark_y), "awry", font=italic, fill="#bdbdbd")
    draw.text((margin_x + awry_w + 6, wordmark_y), "Labs", font=bold, fill="#ffffff")

    # Underline rule
    underline_y = wordmark_y + 138
    draw.rectangle(
        [(margin_x, underline_y), (margin_x + 320, underline_y + 2)],
        fill="#3a3a3a",
    )

    # Tagline
    tag = load_font("regular", 42)
    draw.text((margin_x, 308), "Independent software,", font=tag, fill="#dddddd")
    draw.text((margin_x, 364), "a little off on purpose.", font=tag, fill="#dddddd")

    # Project list — colored dots + names
    dot_y = 510
    label_y = 498
    x = margin_x
    label_font = load_font("regular", 28)

    projects = [
        ("Morass",     "#1D9E75"),
        ("Gravel",     "#378ADD"),
        ("WOPR",       "#00ff41"),
        ("Tyche",      "#FF10F0"),
        ("Embeddings", "#e4c46a"),
    ]

    for i, (name, color) in enumerate(projects):
        if i > 0:
            # Separator dot
            draw.text((x, label_y), "·", font=label_font, fill="#555555")
            x += 28

        r = 11
        draw.ellipse([x, dot_y - r, x + 2 * r, dot_y + r], fill=color)
        x += 2 * r + 12
        draw.text((x, label_y), name, font=label_font, fill="#cccccc")
        x += draw.textlength(name, font=label_font) + 22

    # Footer URL
    url_font = load_font("regular", 26)
    url_w = draw.textlength("awrylabs.com", font=url_font)
    draw.text((W - margin_x - url_w, H - 50 - 26), "awrylabs.com", font=url_font, fill="#777777")

    OUT.parent.mkdir(parents=True, exist_ok=True)
    img.save(OUT, "PNG", optimize=True)
    print(f"wrote {OUT} ({W}x{H})")


if __name__ == "__main__":
    main()
