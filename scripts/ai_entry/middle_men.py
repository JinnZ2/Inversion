"""AI entry handler for Middle-men.md -- institutional corruption of founders' teachings."""

from __future__ import annotations

import sys

try:
    from ._common import MarkdownDoc
except ImportError:
    from pathlib import Path as _P
    sys.path.insert(0, str(_P(__file__).resolve().parents[2]))
    from scripts.ai_entry._common import MarkdownDoc

DOC = MarkdownDoc(
    slug="middle-men",
    path="Middle-men.md",
    category="framework",
    summary=(
        "How institutional middlemen inverted thermodynamically-sound, "
        "reciprocity-based teachings of religious founders into extractive "
        "hierarchies while claiming founder authority."
    ),
    related_scripts=[
        "scripts/systems/dependency_audit.py",
        "scripts/analysis/contamination_detector.py",
    ],
)


if __name__ == "__main__":
    sys.exit(DOC.cli())
