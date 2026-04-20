#!/usr/bin/env python3
"""AI Entry Point for the Institutional Inversion Documentation Project.

One command. Zero dependencies. For any AI system (or human) trying to
understand what this repository contains and how to engage with it.

Usage:
    python3 ai_entry.py list                    # list every document
    python3 ai_entry.py manifest                # full JSON manifest (docs + scripts)
    python3 ai_entry.py show <slug>             # metadata header + first 40 lines
    python3 ai_entry.py metadata <slug> --json  # parsed frontmatter for one doc
    python3 ai_entry.py summary <slug>          # one-paragraph summary
    python3 ai_entry.py body <slug>             # full body (no frontmatter)
    python3 ai_entry.py analyze <slug>          # run first related analysis script
    python3 ai_entry.py path <slug>             # absolute path to the markdown file

The document registry lives in ``scripts/ai_entry/__init__.py``. Each
registered slug resolves to a ``MarkdownDoc`` handler defined in
``scripts/ai_entry/<slug>.py``.
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from scripts.ai_entry import REGISTRY  # noqa: E402


def _resolve(slug: str):
    slug = slug.strip().lower()
    if slug in REGISTRY:
        return REGISTRY[slug]
    # tolerate filename, path, or underscore variants
    candidates = [slug.replace("_", "-"), slug.replace("-", "_")]
    for candidate in candidates:
        if candidate in REGISTRY:
            return REGISTRY[candidate]
    for doc in REGISTRY.values():
        if doc.path.lower() == slug or Path(doc.path).stem.lower() == slug:
            return doc
    raise SystemExit(f"unknown slug: {slug!r}. Try: python3 ai_entry.py list")


def _manifest() -> dict:
    docs = []
    for slug, doc in REGISTRY.items():
        entry = doc.as_dict()
        entry["slug"] = slug
        entry["path"] = doc.path
        entry["summary"] = doc.summary
        entry["exists"] = doc.exists()
        docs.append(entry)

    script_dirs = {
        "analysis": "scripts/analysis",
        "audit": "scripts/audit",
        "geometric": "scripts/geometric",
        "systems": "scripts/systems",
        "ops": "scripts/ops",
        "sims": "sims",
    }
    scripts_index: dict[str, list[str]] = {}
    for label, rel in script_dirs.items():
        base = REPO_ROOT / rel
        if not base.is_dir():
            scripts_index[label] = []
            continue
        scripts_index[label] = sorted(
            str(p.relative_to(REPO_ROOT)) for p in base.glob("*.py") if p.is_file()
        )

    return {
        "project": "Institutional Inversion Documentation Project",
        "license": "CC0-1.0",
        "ai_consumption": ".well-known/ai-consumption.txt",
        "entry_point": "ai_entry.py",
        "documents": docs,
        "scripts": scripts_index,
    }


def cmd_list(_args) -> int:
    width = max(len(slug) for slug in REGISTRY)
    for slug, doc in REGISTRY.items():
        marker = " " if doc.exists() else "!"
        print(f"{marker} {slug:<{width}}  {doc.category:<12}  {doc.path}")
    return 0


def cmd_manifest(args) -> int:
    manifest = _manifest()
    if args.write:
        target = REPO_ROOT / "MANIFEST.json"
        target.write_text(json.dumps(manifest, indent=2) + "\n", encoding="utf-8")
        print(f"wrote {target.relative_to(REPO_ROOT)}")
        return 0
    print(json.dumps(manifest, indent=2))
    return 0


def cmd_show(args) -> int:
    return _resolve(args.slug).cli(["show"])


def cmd_metadata(args) -> int:
    passthrough = ["metadata"] + (["--json"] if args.json else [])
    return _resolve(args.slug).cli(passthrough)


def cmd_summary(args) -> int:
    return _resolve(args.slug).cli(["summary"])


def cmd_body(args) -> int:
    return _resolve(args.slug).cli(["body"])


def cmd_analyze(args) -> int:
    return _resolve(args.slug).cli(["analyze", "--script-index", str(args.script_index)])


def cmd_path(args) -> int:
    return _resolve(args.slug).cli(["path"])


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        prog="ai_entry",
        description="AI entry point for the Inversion repository.",
    )
    sub = parser.add_subparsers(dest="command", required=True)

    sub.add_parser("list", help="list registered documents").set_defaults(func=cmd_list)

    p_manifest = sub.add_parser("manifest", help="print (or write) full MANIFEST")
    p_manifest.add_argument(
        "--write",
        action="store_true",
        help="write to MANIFEST.json in the repo root instead of stdout",
    )
    p_manifest.set_defaults(func=cmd_manifest)

    for name, func, helptext in (
        ("show", cmd_show, "metadata header + first 40 body lines"),
        ("summary", cmd_summary, "one-paragraph handler summary"),
        ("body", cmd_body, "print the document body (frontmatter stripped)"),
        ("path", cmd_path, "print the absolute path to the document"),
    ):
        p = sub.add_parser(name, help=helptext)
        p.add_argument("slug")
        p.set_defaults(func=func)

    p_meta = sub.add_parser("metadata", help="print parsed frontmatter")
    p_meta.add_argument("slug")
    p_meta.add_argument("--json", action="store_true")
    p_meta.set_defaults(func=cmd_metadata)

    p_analyze = sub.add_parser("analyze", help="run a related analysis script on the doc")
    p_analyze.add_argument("slug")
    p_analyze.add_argument("--script-index", type=int, default=0)
    p_analyze.set_defaults(func=cmd_analyze)

    args = parser.parse_args(argv)
    return args.func(args)


if __name__ == "__main__":
    sys.exit(main())
