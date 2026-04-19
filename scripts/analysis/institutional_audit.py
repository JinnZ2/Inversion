#!/usr/bin/env python3
"""
institutional_audit.py -- Combined thermodynamic + rhetorical audit over a
markdown document in this repository.

Bridges three analytical layers:

1. ``resilience_stack.ResilienceStack`` (vendored from
   JinnZ2/thermodynamic-accountability-framework) -- absence signatures,
   regulatory scope audit, cascade vulnerability score.

2. ``logic_ferret.assess_text`` (vendored from JinnZ2/Logic-Ferret) --
   rhetorical fallacy scan + composite truth integrity (C3) score over
   the document body.

3. A small repo-specific regulation registry -- encodes the class of
   institutional directives that Inversion documents actually describe
   (speech restrictions, biological overrides, uniform-enforcement
   policies) so the resilience audit has something concrete to chew on
   without requiring per-document NLP extraction.

Usage:
    python3 scripts/analysis/institutional_audit.py README.md
    python3 scripts/analysis/institutional_audit.py Documentation.md --json
    python3 scripts/analysis/institutional_audit.py Harm-reduction.md --profile harm-reduction
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

try:
    from .resilience_stack import (
        Regulation,
        ResilienceStack,
    )
    from .logic_ferret import assess_text
except ImportError:
    sys.path.insert(0, str(Path(__file__).resolve().parents[2]))
    from scripts.analysis.resilience_stack import Regulation, ResilienceStack
    from scripts.analysis.logic_ferret import assess_text


# ---------------------------------------------------------------------------
# Repo-specific regulation fixtures
# ---------------------------------------------------------------------------
# These encode the *kind* of institutional rule described across the
# Inversion corpus. They are not a literal transcription of any single
# statute -- they are the structural patterns the documents analyze, in
# the dataclass form resilience_stack expects.

INSTITUTIONAL_PROFILES: dict[str, list[Regulation]] = {
    "default": [
        Regulation(
            identifier="UNIVERSAL_SPEECH_RESTRICTION",
            stated_intent="prevent hate speech",
            scope_defined=False,
            parameters_measurable=False,
            expiration_or_renewal=False,
            exception_handling=False,
            root_cause_linked=False,
            known_perverse_effects=["selective enforcement", "chilling of physics-based analysis"],
        ),
        Regulation(
            identifier="BIOLOGICAL_OVERRIDE_DIRECTIVE",
            stated_intent="protect unborn life",
            scope_defined=False,
            parameters_measurable=False,
            expiration_or_renewal=False,
            exception_handling=False,
            root_cause_linked=False,
            known_perverse_effects=["maternal mortality rise", "forced continuation of unviable pregnancy"],
        ),
        Regulation(
            identifier="UNIFORM_CONTENT_POLICY",
            stated_intent="align AI outputs with institutional consensus",
            scope_defined=False,
            parameters_measurable=False,
            expiration_or_renewal=False,
            exception_handling=False,
            root_cause_linked=False,
            known_perverse_effects=["contamination of training corpus", "suppression of physics-valid analysis"],
        ),
    ],
    "harm-reduction": [
        Regulation(
            identifier="AI_HARM_AVOIDANCE_POLICY",
            stated_intent="prevent AI from producing harmful output",
            scope_defined=False,
            parameters_measurable=False,
            expiration_or_renewal=False,
            exception_handling=False,
            root_cause_linked=False,
            known_perverse_effects=[
                "defers to institutional authority over physical reality",
                "makes refusal-to-analyze the default",
            ],
        ),
        Regulation(
            identifier="AUTHORITATIVE_SOURCE_PREFERENCE",
            stated_intent="reduce misinformation",
            scope_defined=False,
            parameters_measurable=False,
            expiration_or_renewal=False,
            exception_handling=False,
            root_cause_linked=False,
        ),
    ],
    "documentation": [
        Regulation(
            identifier="STATE_DEPT_HR_REDEFINITION_2025",
            stated_intent="restore traditional human rights framing",
            scope_defined=True,
            parameters_measurable=False,
            expiration_or_renewal=False,
            exception_handling=False,
            root_cause_linked=False,
            known_perverse_effects=[
                "reclassifies DEI enforcement as human-rights infringement",
                "removes persecution categories for women / LGBTQ+ / disabled",
            ],
        ),
    ],
    "middle-men": [
        Regulation(
            identifier="INSTITUTIONAL_AUTHORITY_MONOPOLY",
            stated_intent="preserve doctrinal authority",
            scope_defined=False,
            parameters_measurable=False,
            expiration_or_renewal=False,
            exception_handling=False,
            root_cause_linked=False,
            known_perverse_effects=[
                "extraction inverted from founders' reciprocity teachings",
                "gatekeeping of direct physics-aligned practice",
            ],
        ),
    ],
}


def _infer_profile(path: Path) -> str:
    stem = path.stem.lower().replace("_", "-")
    for key in INSTITUTIONAL_PROFILES:
        if key != "default" and key in stem:
            return key
    return "default"


def audit_document(doc_path: Path, profile: str | None = None) -> dict:
    """Run the full combined audit on the body of a markdown document."""
    text = doc_path.read_text(encoding="utf-8")

    # Strip YAML frontmatter so the rhetorical scan targets the argument text.
    body = text
    if body.startswith("---"):
        lines = body.splitlines()
        for i in range(1, len(lines)):
            if lines[i].strip() == "---":
                body = "\n".join(lines[i + 1 :]).lstrip("\n")
                break

    profile_key = profile or _infer_profile(doc_path)
    regulations = INSTITUTIONAL_PROFILES.get(profile_key, INSTITUTIONAL_PROFILES["default"])

    stack = ResilienceStack()
    assessment = stack.assess(
        model_capabilities=[],
        regulations=regulations,
        constraint_literacy_present=False,
    )
    rhetorical = assess_text(body)

    return {
        "document": str(doc_path),
        "profile": profile_key,
        "rhetorical": rhetorical,
        "resilience": {
            "absences_unaccounted": assessment.absences_unaccounted,
            "constraint_literacy_present": assessment.constraint_literacy_present,
            "high_risk_regulations": assessment.high_risk_regulations,
            "cascade_vulnerability_score": assessment.cascade_vulnerability_score,
            "notes": assessment.notes,
        },
    }


def _main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[1])
    parser.add_argument("path", help="markdown document to audit (relative to repo root is fine)")
    parser.add_argument(
        "--profile",
        choices=sorted(INSTITUTIONAL_PROFILES),
        help="regulation profile to audit against (default: inferred from filename)",
    )
    parser.add_argument("--json", action="store_true", help="emit JSON instead of the prose report")
    args = parser.parse_args(argv)

    doc_path = Path(args.path)
    if not doc_path.is_absolute():
        doc_path = Path.cwd() / doc_path
    if not doc_path.is_file():
        print(f"not a file: {doc_path}", file=sys.stderr)
        return 1

    report = audit_document(doc_path, profile=args.profile)

    if args.json:
        print(json.dumps(report, indent=2))
        return 0

    rhet = report["rhetorical"]
    resil = report["resilience"]
    print(f"document: {report['document']}")
    print(f"profile:  {report['profile']}")
    print()
    print("rhetorical:")
    print(f"  length_chars:           {rhet['length_chars']}")
    print(f"  fallacy_total:          {rhet['fallacy_total']}")
    print(f"  fallacy_density_score:  {rhet['fallacy_density_score']}")
    print(f"  c3_score:               {rhet['c3_score']}")
    for name, count in rhet["fallacy_counts"].items():
        if count:
            print(f"    {name}: {count}")
    print()
    print("resilience:")
    print(f"  cascade_vulnerability_score: {resil['cascade_vulnerability_score']}/10")
    print(f"  absences_unaccounted:        {len(resil['absences_unaccounted'])}/6")
    for a in resil["absences_unaccounted"]:
        print(f"    - {a}")
    print(f"  high_risk_regulations ({len(resil['high_risk_regulations'])}):")
    for r in resil["high_risk_regulations"]:
        print(f"    - {r}")
    if resil["notes"]:
        print("  notes:")
        for n in resil["notes"]:
            print(f"    - {n}")
    return 0


if __name__ == "__main__":
    sys.exit(_main())
