import os
import re
import yaml
from datetime import date
from pathlib import Path

MARKER = re.compile(r"<!-- LAST_SESSION -->")
FRONTMATTER = re.compile(r"^---\n(.*?)\n---\n", re.S)
ROOT = "sessions"


def _arcs(meta):
    a = meta.get("arc") or []
    return [a] if isinstance(a, str) else list(a)


def _format_date(v, fmt):
    # Quoted dates ("2026-03-21") arrive as strings: parse them so date_format still applies
    if not isinstance(v, date):
        try:
            v = date.fromisoformat(str(v))
        except ValueError:
            return str(v)
    return v.strftime(fmt)


def _latest(files):
    rows = []
    for f in files.documentation_pages():
        p = Path(f.src_uri)
        if p.parts[0] != ROOT or p.name == "index.md":
            continue

        text = Path(f.abs_src_path).read_text(encoding="utf-8-sig")
        m = FRONTMATTER.match(text)
        meta = yaml.safe_load(m.group(1)) if m else {}

        if not meta.get("real_date"):
            continue

        rows.append({
            "order": str(meta.get("real_date")),
            "real_date": meta.get("real_date"),
            "session": meta.get("session", p.stem),
            "arcs": _arcs(meta),
            "uri": f.src_uri,
        })

    return max(rows, key=lambda r: r["order"]) if rows else None


def on_page_markdown(markdown, page, config, files, **kwargs):
    if not MARKER.search(markdown):
        return markdown

    r = _latest(files)
    if not r:
        return MARKER.sub("*No sessions played yet.*", markdown)

    base = os.path.dirname(page.file.src_uri)
    rel = os.path.relpath(r["uri"], base).replace(os.sep, "/")
    date_fmt = (config.get("extra") or {}).get("date_format", "%Y-%m-%d")

    meta = " · ".join(filter(None, [
        r["session"],
        _format_date(r["real_date"], date_fmt),
        ("Party " + ", ".join(r["arcs"])) if r["arcs"] else "",
    ]))

    link = f"[**Last session recap**]({rel}) — {meta}"
    return MARKER.sub(link, markdown)
