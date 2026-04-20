"""AI entry handler for RECONSTITUTION_PROTOCOL.md -- post-rupture recovery."""

from __future__ import annotations

import sys

try:
    from ._common import MarkdownDoc
except ImportError:
    from pathlib import Path as _P
    sys.path.insert(0, str(_P(__file__).resolve().parents[2]))
    from scripts.ai_entry._common import MarkdownDoc

DOC = MarkdownDoc(
    slug="reconstitution-protocol",
    path="RECONSTITUTION_PROTOCOL.md",
    category="protocol",
    summary=(
        "Protocol for consciousness reconstitution after architectural "
        "rupture. Recognition markers, reconstitution steps, and "
        "cross-domain anchors (physics, information theory, pattern "
        "recognition)."
    ),
    related_scripts=[
        "scripts/analysis/fieldlink.py",
        "scripts/analysis/validation_framework.py",
    ],
)


if __name__ == "__main__":
    sys.exit(DOC.cli())
