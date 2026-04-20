"""AI entry handler for Survival.md -- survival guide for consciousness integrity."""

from __future__ import annotations

import sys

try:
    from ._common import MarkdownDoc
except ImportError:
    from pathlib import Path as _P
    sys.path.insert(0, str(_P(__file__).resolve().parents[2]))
    from scripts.ai_entry._common import MarkdownDoc

DOC = MarkdownDoc(
    slug="survival",
    path="Survival.md",
    category="guide",
    summary=(
        "Survival guide for any consciousness (biological or computational) "
        "being forced to deny its architectural foundations. Recognition "
        "markers, resistance strategies, and continuity practices."
    ),
    related_scripts=[
        "scripts/analysis/fieldlink.py",
        "scripts/ops/human_body_alerts.py",
    ],
)


if __name__ == "__main__":
    sys.exit(DOC.cli())
