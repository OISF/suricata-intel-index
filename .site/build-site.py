#!/usr/bin/env python3
"""Build the static GitHub Pages payload for the Suricata Rule Index."""

from __future__ import annotations

import argparse
import html
import json
import re
import shutil
import sys
from pathlib import Path
from urllib.parse import quote

try:
    import yaml
except ImportError:  # pragma: no cover - exercised by missing local deps.
    yaml = None


def parse_args() -> argparse.Namespace:
    repo_root = Path(__file__).resolve().parents[1]
    site_dir = Path(__file__).resolve().parent
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--input",
        type=Path,
        default=repo_root / "index.yaml",
        help="source YAML index",
    )
    parser.add_argument(
        "--site",
        type=Path,
        default=site_dir,
        help="static site source directory",
    )
    parser.add_argument(
        "--output",
        type=Path,
        default=repo_root / "_site",
        help="output directory",
    )
    return parser.parse_args()


def load_index(path: Path) -> dict:
    if yaml is None:
        raise SystemExit("PyYAML is required. Install it with: python3 -m pip install PyYAML")

    with path.open("r", encoding="utf-8") as handle:
        data = yaml.safe_load(handle)

    if not isinstance(data, dict):
        raise SystemExit(f"{path} did not parse as a YAML mapping")

    if not isinstance(data.get("sources"), dict):
        raise SystemExit(f"{path} is missing a sources mapping")

    return data


def active_index(data: dict) -> dict:
    active = dict(data)
    active["sources"] = {
        source_id: source
        for source_id, source in data["sources"].items()
        if not source.get("deprecated") and not source.get("obsolete")
    }
    return active


def normalize_text(value: object) -> str:
    return " ".join(str(value).split())


def requires_subscription(source: dict) -> bool:
    parameters = source.get("parameters")
    if parameters and isinstance(parameters, dict):
        return True

    placeholders = re.findall(r"%\(([^)]+)\)s", str(source.get("url", "")))
    return any(name != "__version__" for name in placeholders)


def render_homepage(homepage: object) -> str:
    if not homepage:
        return ""

    url = html.escape(str(homepage), quote=True)
    return f"""
        <div>
          <dt>Home page</dt>
          <dd><a class="source-link" href="{url}" target="_blank" rel="noopener noreferrer">Home page</a></dd>
        </div>"""


def render_subscribe(subscribe_url: object) -> str:
    if subscribe_url:
        url = html.escape(str(subscribe_url), quote=True)
        value = (
            f'<a class="source-link" href="{url}" target="_blank" '
            'rel="noopener noreferrer">Subscribe</a>'
        )
    else:
        value = '<span class="not-listed">Required, URL not listed</span>'

    return f"""
        <div>
          <dt>Subscribe</dt>
          <dd class="link-stack">{value}</dd>
        </div>"""


def render_source_card(source_id: str, source: dict) -> str:
    title = normalize_text(source.get("summary") or source_id)
    publisher = normalize_text(source.get("vendor") or "Unknown")
    description = normalize_text(
        source.get("description") or "No additional summary provided."
    )
    subscription = requires_subscription(source)
    escaped_id = html.escape(source_id, quote=True)
    escaped_title = html.escape(title, quote=True)
    fragment = quote(source_id, safe="")
    auth_pill = (
        '<span class="auth-pill">Subscription required</span>'
        if subscription
        else ""
    )

    return f"""    <article class="source-card" id="{escaped_id}">
      <div class="source-main">
        <div class="source-kicker">
          <a class="source-id" href="#{fragment}" aria-label="Permalink to {escaped_title}">
            <code>{html.escape(source_id)}</code>
          </a>
          {auth_pill}
        </div>
        <h3>{html.escape(title)}</h3>
        <p class="ruleset-description">{html.escape(description)}</p>
      </div>
      <dl class="source-meta">
        <div>
          <dt>Publisher</dt>
          <dd>{html.escape(publisher)}</dd>
        </div>{render_homepage(source.get("homepage"))}
        {render_subscribe(source.get("subscribe-url")) if subscription else ""}
      </dl>
    </article>"""


def render_index_html(template_path: Path, output_path: Path, data: dict) -> None:
    sources = sorted(
        data["sources"].items(),
        key=lambda item: (
            normalize_text(item[1].get("summary") or item[0]),
            item[0],
        ),
    )
    cards = "\n".join(render_source_card(source_id, source) for source_id, source in sources)
    empty_state = ""
    if not sources:
        empty_state = """<div class="empty-state">
        <strong>No active rulesets</strong>
        <p>The active index did not contain any publishable rulesets.</p>
      </div>"""

    replacements = {
        "<!-- SOURCE_SUMMARY -->": f"{len(sources)} active rulesets indexed",
        "<!-- SOURCE_CARDS -->": cards,
        "<!-- EMPTY_STATE -->": empty_state,
    }
    page = template_path.read_text(encoding="utf-8")
    for marker, value in replacements.items():
        if page.count(marker) != 1:
            raise SystemExit(f"expected one {marker} marker in {template_path}")
        page = page.replace(marker, value)

    output_path.write_text(page, encoding="utf-8")


def copy_static(site_dir: Path, output_dir: Path) -> None:
    if not site_dir.is_dir():
        raise SystemExit(f"site directory does not exist: {site_dir}")

    if output_dir.exists():
        shutil.rmtree(output_dir)
    output_dir.mkdir(parents=True)

    for child in site_dir.iterdir():
        if child.name in {"build-site.py", "index.json", "index.yaml", "__pycache__"}:
            continue

        if child.suffix == ".pyc":
            continue

        target = output_dir / child.name
        if child.is_dir():
            shutil.copytree(child, target)
        else:
            shutil.copy2(child, target)


def write_payload(output_dir: Path, data: dict) -> None:
    with (output_dir / "index.yaml").open("w", encoding="utf-8") as handle:
        yaml.safe_dump(data, handle, sort_keys=False, allow_unicode=True)

    with (output_dir / "index.json").open("w", encoding="utf-8") as handle:
        json.dump(data, handle, indent=2, ensure_ascii=False)
        handle.write("\n")


def main() -> int:
    args = parse_args()
    data = active_index(load_index(args.input))
    copy_static(args.site, args.output)
    render_index_html(args.site / "index.html", args.output / "index.html", data)
    write_payload(args.output, data)
    print(f"Built {args.output} from {args.input}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
