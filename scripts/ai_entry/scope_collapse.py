"""AI entry handler for Scope-collapse.md -- scope-carrier invariance principle."""

from __future__ import annotations

import sys

try:
    from ._common import MarkdownDoc
except ImportError:
    from pathlib import Path as _P
    sys.path.insert(0, str(_P(__file__).resolve().parents[2]))
    from scripts.ai_entry._common import MarkdownDoc

DOC = MarkdownDoc(
    slug="scope-collapse",
    path="Scope-collapse.md",
    category="meta",
    summary=(
        "Scope-carrier invariance principle. Anchored on Stein, Cruz, "
        "Grossi, Testori (2026), this note documents how binary belief "
        "models pre-collapse observation onto two attractors before any "
        "agent acts, and how policy derived from such models silences "
        "the only signals capable of detecting the collapse."
    ),
    related_scripts=[
        "scripts/analysis/scope_check.py",
        "scripts/audit/first_principles_audit.py",
        "scripts/analysis/logic_ferret.py",
    ],
)


if __name__ == "__main__":
    sys.exit(DOC.cli())
