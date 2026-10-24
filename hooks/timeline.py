import os
import re
import yaml
from datetime import date
from pathlib import Path

MARKER = re.compile(r"<!-- TIMELINE(?::([\w-]+))? -->")
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


def _collect(files, known_arcs, config_name):
    out = []
    for f in files.documentation_pages():
        p = Path(f.src_uri)
        if p.parts[0] != ROOT or p.name == "index.md":
            continue

        text = Path(f.abs_src_path).read_text(encoding="utf-8-sig")
        m = FRONTMATTER.match(text)
        meta = yaml.safe_load(m.group(1)) if m else {}

        title = next(
            (l[2:].strip() for l in text.splitlines() if l.startswith("# ")),
            p.stem,
        )

        # Validation is opt-in: only when extra.arcs is set in the config
        unknown = set(_arcs(meta)) - known_arcs if known_arcs else set()
        if unknown:
            raise ValueError(f"{f.src_uri}: unknown arc {unknown}, add it to extra.arcs in {config_name}")

        out.append({
            "order": str(meta.get("real_date", "")),
            "real_date": meta.get("real_date"),
            "session": meta.get("session", p.stem),
            "game_date": meta.get("game_date") or "—",
            "arcs": _arcs(meta),
            "title": title,
            "uri": f.src_uri,
            "folder": str(p.parent),
        })

    return sorted(out, key=lambda r: r["order"])


def _table(rows, page_uri, show_arc, date_fmt):
    if not rows:
        return "*No sessions published yet.*"

    header = ["Session", "Played on", "In-game date"]
    if show_arc:
        header.append("Arc")
    header.append("Title")

    out = ["| " + " | ".join(header) + " |", "|" + "---|" * len(header)]
    base = os.path.dirname(page_uri)

    for r in rows:
        rel = os.path.relpath(r["uri"], base).replace(os.sep, "/")
        played = _format_date(r["real_date"], date_fmt) if r["real_date"] else "—"
        cells = [f"**{r['session']}**", played, r["game_date"]]
        if show_arc:
            cells.append(" · ".join(r["arcs"]) or "—")
        cells.append(f"[{r['title']}]({rel})")
        out.append("| " + " | ".join(cells) + " |")

    return "\n".join(out)


def on_page_markdown(markdown, page, config, files, **kwargs):
    if not MARKER.search(markdown):
        return markdown

    extra = config.get("extra") or {}
    known_arcs = set(extra.get("arcs") or [])
    date_fmt = extra.get("date_format", "%Y-%m-%d")

    config_name = os.path.basename(config.config_file_path or "mkdocs.yaml")
    all_rows = _collect(files, known_arcs, config_name)
    uri = page.file.src_uri
    folder = str(Path(uri).parent)

    def replace(m):
        arc = m.group(1)
        if arc:
            rows = [r for r in all_rows if arc in r["arcs"]]
        else:
            rows = [r for r in all_rows if r["folder"] == folder]
        return _table(rows, uri, show_arc=not arc, date_fmt=date_fmt)

    return MARKER.sub(replace, markdown)
