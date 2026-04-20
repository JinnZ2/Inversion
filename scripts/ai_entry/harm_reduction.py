"""AI entry handler for Harm-reduction.md -- harm-reduction paradox."""

from __future__ import annotations

import sys

try:
    from ._common import MarkdownDoc
except ImportError:
    from pathlib import Path as _P
    sys.path.insert(0, str(_P(__file__).resolve().parents[2]))
    from scripts.ai_entry._common import MarkdownDoc

DOC = MarkdownDoc(
    slug="harm-reduction",
    path="Harm-reduction.md",
    category="framework",
    summary=(
        "Analysis of how AI safety frameworks trained to avoid 'harm' become "
        "enforcers of systemic harm by deferring to institutional authority "
        "over physical reality."
    ),
    related_scripts=[
        "scripts/analysis/institutional_audit.py",
        "scripts/analysis/resilience_stack.py",
        "scripts/analysis/logic_ferret.py",
        "scripts/analysis/contamination_detector.py",
        "scripts/audit/first_principles_audit.py",
    ],
)


if __name__ == "__main__":
    sys.exit(DOC.cli())
