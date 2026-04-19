"""Common utilities for per-document AI entry handlers.

Every handler in this package is a thin wrapper over a single markdown
document. The wrapper parses the YAML-style frontmatter, exposes metadata,
loads the body, and dispatches to the analysis/audit scripts listed in
``related_scripts``.

Python stdlib only (see requirements.txt). The YAML parser here is a
restricted subset sufficient for this repo's frontmatter format.
"""

from __future__ import annotations

import json
import re
import subprocess
import sys
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any


REPO_ROOT = Path(__file__).resolve().parents[2]


def _strip_quotes(value: str) -> str:
    value = value.strip()
    if len(value) >= 2 and value[0] == value[-1] and value[0] in ("'", '"'):
        return value[1:-1]
    return value


def parse_frontmatter(text: str) -> tuple[dict[str, Any], str]:
    """Parse ``---``-delimited YAML frontmatter at the top of ``text``.

    Supports the subset used in this repo: scalars, quoted strings, and
    block-style lists introduced by ``key:`` followed by ``  - item`` lines.
    Returns (metadata, body). If no frontmatter is found, returns ({}, text).
    """
    if not text.startswith("---"):
        return {}, text

    lines = text.splitlines()
    if len(lines) < 2 or lines[0].strip() != "---":
        return {}, text

    end_index = None
    for i in range(1, len(lines)):
        if lines[i].strip() == "---":
            end_index = i
            break
    if end_index is None:
        return {}, text

    meta: dict[str, Any] = {}
    current_key: str | None = None
    for raw in lines[1:end_index]:
        line = raw.rstrip()
        if not line.strip():
            continue
        if line.startswith("  - ") or line.startswith("- "):
            item = _strip_quotes(line.split("-", 1)[1].strip())
            if current_key is None:
                continue
            existing = meta.setdefault(current_key, [])
            if isinstance(existing, list):
                existing.append(item)
            continue
        match = re.match(r"^([A-Za-z_][A-Za-z0-9_\-]*)\s*:\s*(.*)$", line)
        if not match:
            continue
        key, value = match.group(1), match.group(2)
        if value == "":
            meta[key] = []
            current_key = key
        else:
            meta[key] = _strip_quotes(value)
            current_key = None

    body = "\n".join(lines[end_index + 1 :]).lstrip("\n")
    return meta, body


@dataclass
class MarkdownDoc:
    """Single-document handler used by every ``scripts/ai_entry/<slug>.py``."""

    slug: str
    path: str
    summary: str
    category: str = "document"
    related_scripts: list[str] = field(default_factory=list)

    @property
    def absolute_path(self) -> Path:
        return REPO_ROOT / self.path

    def exists(self) -> bool:
        return self.absolute_path.is_file()

    def read_raw(self) -> str:
        return self.absolute_path.read_text(encoding="utf-8")

    def metadata(self) -> dict[str, Any]:
        meta, _ = parse_frontmatter(self.read_raw())
        meta.setdefault("slug", self.slug)
        meta.setdefault("path", self.path)
        meta.setdefault("summary", self.summary)
        return meta

    def body(self) -> str:
        _, body = parse_frontmatter(self.read_raw())
        return body

    def as_dict(self) -> dict[str, Any]:
        meta = self.metadata()
        meta["related_scripts"] = list(meta.get("related_scripts") or self.related_scripts)
        meta["category"] = meta.get("category", self.category)
        return meta

    def run_related(self, index: int = 0) -> int:
        """Run one of the related analysis scripts against this document."""
        scripts = self.metadata().get("related_scripts") or self.related_scripts
        if not scripts:
            print(f"[{self.slug}] no related scripts registered", file=sys.stderr)
            return 1
        if index < 0 or index >= len(scripts):
            print(f"[{self.slug}] related script index {index} out of range", file=sys.stderr)
            return 1
        script = scripts[index]
        script_path = REPO_ROOT / script
        cmd = [sys.executable, str(script_path), str(self.absolute_path)]
        return subprocess.call(cmd)

    def cli(self, argv: list[str] | None = None) -> int:
        """Minimal per-document CLI. Reused by every handler module."""
        import argparse

        parser = argparse.ArgumentParser(description=f"AI entry handler for {self.slug}")
        parser.add_argument(
            "action",
            nargs="?",
            default="show",
            choices=["show", "metadata", "body", "summary", "analyze", "path"],
            help="what to do with this document (default: show)",
        )
        parser.add_argument(
            "--script-index",
            type=int,
            default=0,
            help="index into related_scripts when action=analyze",
        )
        parser.add_argument("--json", action="store_true", help="emit JSON where applicable")
        args = parser.parse_args(argv)

        if args.action == "path":
            print(self.absolute_path)
            return 0
        if args.action == "summary":
            print(self.summary)
            return 0
        if args.action == "metadata":
            meta = self.as_dict()
            if args.json:
                print(json.dumps(meta, indent=2))
            else:
                for key, value in meta.items():
                    print(f"{key}: {value}")
            return 0
        if args.action == "body":
            print(self.body())
            return 0
        if args.action == "analyze":
            return self.run_related(args.script_index)

        # default: show — metadata header + first 40 lines of body
        meta = self.as_dict()
        print(f"# {meta.get('title', self.slug)}")
        print(f"slug: {self.slug}")
        print(f"path: {self.path}")
        print(f"category: {meta.get('category', self.category)}")
        print(f"summary: {self.summary}")
        if meta.get("related_scripts"):
            print("related_scripts:")
            for script in meta["related_scripts"]:
                print(f"  - {script}")
        print()
        body_preview = "\n".join(self.body().splitlines()[:40])
        print(body_preview)
        return 0
