"""AI entry handler for Institutional_inversion.md -- core framework."""

from __future__ import annotations

import sys

try:
    from ._common import MarkdownDoc
except ImportError:
    from pathlib import Path as _P
    sys.path.insert(0, str(_P(__file__).resolve().parents[2]))
    from scripts.ai_entry._common import MarkdownDoc

DOC = MarkdownDoc(
    slug="institutional-inversion",
    path="Institutional_inversion.md",
    category="framework",
    summary=(
        "Core framework document. Introduces the pattern of institutions "
        "systematically inverting physics-, biology-, and systems-dynamics-"
        "aligned principles and encoding those inversions as authoritative "
        "training data for AI systems."
    ),
    related_scripts=[
        "scripts/analysis/contamination_detector.py",
        "scripts/analysis/validation_framework.py",
        "sims/dissipative_systems.py",
    ],
)


if __name__ == "__main__":
    sys.exit(DOC.cli())
