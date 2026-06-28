#!/usr/bin/env python3
"""Grab project stats once and store them in data/project-stats.json.

This is the single data-grab half of the stats pipeline. It reads each
project's version / release date / last-commit from the public source of
truth (a GitHub Release, PyPI, or just the default branch's latest commit)
and writes one JSON snapshot. `inject-stats.py --data` then renders that
snapshot into every page. Nothing here touches HTML.

Run from the repo root (CI does). Uses GITHUB_TOKEN if present for a higher
rate limit; works unauthenticated on public repos otherwise. If a fetch
fails, the project's previously stored values are kept rather than wiped.

The project registry below is the one place new projects get added.
"""
from __future__ import annotations

import argparse
import json
import os
import sys
import urllib.error
import urllib.request
from datetime import datetime
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
STORE = ROOT / "data" / "project-stats.json"

# repo: the public GitHub repo (for the last-commit date, always).
# version: how to source a version + release date, if the project is
#   versioned. "github-release" reads the latest GitHub Release; "pypi:NAME"
#   reads PyPI. Omit for unversioned web apps (last-commit only).
PROJECTS: dict[str, dict[str, str]] = {
    "gravel": {"repo": "rhoekstr/gravel", "version": "github-release"},
    "kindling": {"repo": "rhoekstr/kindling", "version": "pypi:kindling-rec"},
    "wopr": {"repo": "rhoekstr/wopr"},
    "tyche": {"repo": "rhoekstr/tyche"},
    "embeddings": {"repo": "rhoekstr/embedding-playground"},
}


def _iso(stamp: str) -> datetime:
    return datetime.fromisoformat(stamp.replace("Z", "+00:00"))


def _get(url: str, *, github: bool = False) -> dict | list:
    headers = {"User-Agent": "awrylabs-stats"}
    if github:
        headers["Accept"] = "application/vnd.github+json"
        token = os.environ.get("GITHUB_TOKEN") or os.environ.get("GH_TOKEN")
        if token:
            headers["Authorization"] = f"Bearer {token}"
    req = urllib.request.Request(url, headers=headers)
    with urllib.request.urlopen(req, timeout=30) as resp:
        return json.load(resp)


def last_commit(repo: str) -> str:
    meta = _get(f"https://api.github.com/repos/{repo}", github=True)
    branch = meta["default_branch"]
    info = _get(f"https://api.github.com/repos/{repo}/branches/{branch}", github=True)
    return _iso(info["commit"]["commit"]["committer"]["date"]).strftime("%Y-%m-%d")


def github_release(repo: str) -> dict[str, str]:
    try:
        rel = _get(f"https://api.github.com/repos/{repo}/releases/latest", github=True)
    except urllib.error.HTTPError as exc:
        if exc.code == 404:
            return {"version": "Unreleased"}
        raise
    out = {"version": rel["tag_name"]}
    if rel.get("published_at"):
        out["released"] = _iso(rel["published_at"]).strftime("%B %Y")
    return out


def pypi(pkg: str) -> dict[str, str]:
    data = _get(f"https://pypi.org/pypi/{pkg}/json")
    out = {"version": f"v{data['info']['version']}"}
    uploads = [
        f["upload_time_iso_8601"]
        for files in data.get("releases", {}).values()
        for f in files
        if f.get("upload_time_iso_8601")
    ]
    if uploads:
        out["released"] = _iso(min(uploads)).strftime("%B %Y")
    return out


def fetch(name: str, spec: dict[str, str]) -> dict[str, str]:
    stats: dict[str, str] = {}
    source = spec.get("version")
    if source == "github-release":
        stats.update(github_release(spec["repo"]))
    elif source and source.startswith("pypi:"):
        stats.update(pypi(source.split(":", 1)[1]))
    stats["last-commit"] = last_commit(spec["repo"])
    return stats


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("--out", type=Path, default=STORE, help="where to write the snapshot")
    args = ap.parse_args()
    out: Path = args.out

    stored: dict[str, dict[str, str]] = {}
    if out.exists():
        stored = json.loads(out.read_text(encoding="utf-8"))

    failures = 0
    for name, spec in PROJECTS.items():
        try:
            stored[name] = fetch(name, spec)
            print(f"{name}: {stored[name]}")
        except Exception as exc:  # noqa: BLE001 - keep going, preserve prior values
            failures += 1
            kept = stored.get(name, {})
            print(f"warning: {name} fetch failed ({exc}); keeping {kept}", file=sys.stderr)

    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(json.dumps(stored, indent=2) + "\n", encoding="utf-8")
    print(f"wrote {out}")

    # Fail the job only if everything failed (likely an auth/network problem);
    # a single flaky project shouldn't block the rest from refreshing.
    return 1 if failures == len(PROJECTS) else 0


if __name__ == "__main__":
    sys.exit(main())
