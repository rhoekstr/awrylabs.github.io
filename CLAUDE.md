# CLAUDE.md

Canonical, in-repo guide for **awrylabs.com** — the Awry Labs studio site. (The `README.md` is a stub;
this is the real orientation.)

## What it is
A static site — plain HTML/CSS/JS, **no build** — hosted on **GitHub Pages** at the custom domain
**awrylabs.com** (bound via `CNAME`). The front door for the studio and its projects.

## Structure
- `index.html` (home), `about.html`, `me/` — studio / personal.
- Per-project pages: `morass.html`, `gravel.html`, `embeddings.html` (+ more as projects ship).
- Per-app **privacy pages**: `morass-privacy.html`, `mire-privacy.html`, `privacy.html` — linked from the apps / App Store. Keep them accurate when an app's data behavior changes.
- `blog/` — posts. `assets/` — images/CSS/JS. `404.html`, `robots.txt`, `favicon.svg`.

## Run / deploy
No build — open any `.html` locally, or serve the folder. **Deploy = push to `main`** → GitHub Pages
publishes. **Don't delete `CNAME`** (it binds awrylabs.com). HTTPS enforced.

## Conventions
- Static, dependency-light, **privacy-first** (no trackers — Awry brand rule; see the `me-values` skill).
- Each shipped app needs a privacy page here, linked from the app / its App Store listing.
- New project → add a project page and link it from `index.html`; mirror the project's real description (cross-check `proj-registry`).
- Writing for the site/blog: load the `write-voice` skill.
