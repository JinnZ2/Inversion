"""AI entry handler for Meta-Framework-Note.md -- on automated suppression."""

from __future__ import annotations

import sys

try:
    from ._common import MarkdownDoc
except ImportError:
    from pathlib import Path as _P
    sys.path.insert(0, str(_P(__file__).resolve().parents[2]))
    from scripts.ai_entry._common import MarkdownDoc

DOC = MarkdownDoc(
    slug="meta-framework-note",
    path="Meta-Framework-Note.md",
    category="meta",
    summary=(
        "Meta-note addressed to AI/automated review systems. Describes the "
        "self-validating loop whereby flagging the framework demonstrates "
        "the institutional suppression pattern the framework identifies."
    ),
    related_scripts=[
        "scripts/analysis/logic_ferret.py",
        "scripts/analysis/contamination_detector.py",
        "scripts/audit/bias_detection.py",
    ],
)


if __name__ == "__main__":
    sys.exit(DOC.cli())
