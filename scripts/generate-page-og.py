#!/usr/bin/env python3
"""Generate per-page OpenGraph / Twitter share cards (1200x630 PNG).

One branded card per project page and per Stories backstory, so social shares
get a relevant image instead of the generic site card. Output: assets/og/<slug>.png.

Run manually when titles, taglines, or the project/story list change:

    python3 scripts/generate-page-og.py

macOS system fonts; falls back to PIL default if a path is missing.
"""
from __future__ import annotations
from pathlib import Path
from PIL import Image, ImageDraw, ImageFont

W, H = 1200, 630
OUT_DIR = Path(__file__).parent.parent / "assets" / "og"
BG = "#0b0b0d"
INK = "#f3f3f3"
MUTE = "#8a8a90"
WORD_GRAY = "#bdbdbd"
MARGIN = 96

FONTS = {
    "bold": ["/System/Library/Fonts/Supplemental/Arial Bold.ttf", "/System/Library/Fonts/HelveticaNeue.ttc", "/Library/Fonts/Arial Bold.ttf"],
    "reg":  ["/System/Library/Fonts/Supplemental/Arial.ttf", "/System/Library/Fonts/Helvetica.ttc"],
    "ital": ["/System/Library/Fonts/Supplemental/Georgia Italic.ttf", "/System/Library/Fonts/Supplemental/Times New Roman Italic.ttf"],
}

def font(kind: str, size: int) -> ImageFont.FreeTypeFont:
    for p in FONTS[kind]:
        if Path(p).exists():
            try: return ImageFont.truetype(p, size)
            except OSError: continue
    return ImageFont.load_default()

def wrap(draw, text, fnt, max_w):
    words, lines, cur = text.split(), [], ""
    for w in words:
        t = (cur + " " + w).strip()
        if draw.textlength(t, font=fnt) <= max_w: cur = t
        else:
            if cur: lines.append(cur)
            cur = w
    if cur: lines.append(cur)
    return lines

def fit(draw, text, max_w, max_lines, start, lo, kind="bold"):
    size = start
    while size >= lo:
        f = font(kind, size)
        ls = wrap(draw, text, f, max_w)
        if len(ls) <= max_lines: return f, ls, size
        size -= 4
    f = font(kind, lo)
    return f, wrap(draw, text, f, max_w), lo

def card(slug, eyebrow, title, subtitle, accent, path):
    img = Image.new("RGB", (W, H), BG)
    d = ImageDraw.Draw(img)
    # left accent bar
    d.rectangle([(0, 0), (12, H)], fill=accent)
    # wordmark
    wm_y, wm_size = 60, 46
    it, bd = font("ital", wm_size), font("bold", wm_size)
    aw = d.textlength("awry", font=it)
    d.text((MARGIN, wm_y), "awry", font=it, fill=WORD_GRAY)
    d.text((MARGIN + aw + 4, wm_y), "Labs", font=bd, fill=INK)
    # eyebrow
    d.text((MARGIN, 182), eyebrow.upper(), font=font("reg", 28), fill=accent)
    max_w = W - MARGIN - 80
    # title (auto-fit)
    tf, tlines, tsize = fit(d, title, max_w, 3, 96, 52)
    y = 226
    for ln in tlines:
        d.text((MARGIN, y), ln, font=tf, fill=INK)
        y += int(tsize * 1.12)
    # subtitle
    if subtitle:
        sf = font("reg", 34)
        for ln in wrap(d, subtitle, sf, max_w)[:2]:
            d.text((MARGIN, y + 14), ln, font=sf, fill=MUTE)
            y += int(34 * 1.3)
    # footer url
    uf = font("reg", 27)
    d.text((MARGIN, H - 78), f"awrylabs.com/{path}", font=uf, fill=MUTE)
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    out = OUT_DIR / f"{slug}.png"
    img.save(out, "PNG", optimize=True)
    print(f"  {out.name:42} ({tsize}px title, {len(tlines)} line{'s' if len(tlines)!=1 else ''})")

PROJECTS = [
    ("morass", "Game · iOS, iPadOS, macOS, watchOS", "Morass", "A calm strategy game about the complexity of power.", "#28b487", "morass"),
    ("gravel", "C++ / Python library", "Gravel", "Network-graph fragility: where is a place one closure from cut off?", "#5a9cd6", "gravel"),
    ("wopr", "Web · React", "WOPR", "Five strategy games, and a war sim whose best ending is not playing.", "#00ff41", "wopr"),
    ("tyche", "Web · React + TypeScript", "Tyche", "A psychedelic randomizer for the small decisions you can't make.", "#ff3df0", "tyche"),
    ("embeddings", "Web · Vanilla JS", "Embedding Playground", "Meaning is geometry. Play with real word vectors in your browser.", "#e4c46a", "embeddings"),
]

STORIES = [
    ("the-line-you-cant-draw", "Backstory · Morass", "The line you can't quite draw", "", "#d08a5e", "stories/the-line-you-cant-draw"),
    ("the-question-routing-doesnt-ask", "Backstory · Gravel", "The question routing libraries don't ask", "", "#5a9cd6", "stories/the-question-routing-doesnt-ask"),
    ("the-only-winning-move", "Backstory · WOPR", "The only winning move", "", "#3fbf63", "stories/the-only-winning-move"),
    ("outsourcing-the-small-decisions", "Backstory · Tyche", "Outsourcing the small decisions", "", "#bd7df0", "stories/outsourcing-the-small-decisions"),
    ("meaning-is-geometry", "Backstory · Embedding Playground", "Meaning is geometry", "", "#e4c46a", "stories/meaning-is-geometry"),
]

def main():
    print("projects:")
    for slug, eb, ti, sub, acc, path in PROJECTS:
        card(slug, eb, ti, sub, acc, path)
    print("stories:")
    for slug, eb, ti, sub, acc, path in STORIES:
        card(slug, eb, ti, sub, acc, path)

if __name__ == "__main__":
    main()
