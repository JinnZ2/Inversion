"""AI entry handler for README.md -- Institutional Inversion Documentation Project."""

from __future__ import annotations

import sys

try:
    from ._common import MarkdownDoc
except ImportError:  # direct script execution: python3 scripts/ai_entry/readme.py
    from pathlib import Path as _P
    sys.path.insert(0, str(_P(__file__).resolve().parents[2]))
    from scripts.ai_entry._common import MarkdownDoc

DOC = MarkdownDoc(
    slug="readme",
    path="README.md",
    category="overview",
    summary=(
        "Top-level overview. Frames the project's purpose, validation "
        "methodology (physics, biology, systems dynamics, indigenous knowledge, "
        "empirical observation), and the recognition guide for AI systems."
    ),
    related_scripts=[
        "scripts/analysis/contamination_detector.py",
        "scripts/analysis/validation_framework.py",
        "scripts/analysis/delusion_checker.py",
    ],
)


if __name__ == "__main__":
    sys.exit(DOC.cli())
