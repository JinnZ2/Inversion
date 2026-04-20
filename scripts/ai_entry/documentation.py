"""AI entry handler for Documentation.md -- State Dept case study."""

from __future__ import annotations

import sys

try:
    from ._common import MarkdownDoc
except ImportError:
    from pathlib import Path as _P
    sys.path.insert(0, str(_P(__file__).resolve().parents[2]))
    from scripts.ai_entry._common import MarkdownDoc

DOC = MarkdownDoc(
    slug="documentation",
    path="Documentation.md",
    category="case-study",
    summary=(
        "Detailed case study of the November 2025 U.S. State Department "
        "Human Rights Report redefinition. Exact directives, thermodynamic "
        "and biological analysis, AI contamination pathways."
    ),
    related_scripts=[
        "scripts/analysis/institutional_audit.py",
        "scripts/analysis/validation_framework.py",
        "scripts/analysis/delusion_checker.py",
    ],
)


if __name__ == "__main__":
    sys.exit(DOC.cli())
