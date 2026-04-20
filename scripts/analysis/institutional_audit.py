#!/usr/bin/env python3
"""
institutional_audit.py -- Combined thermodynamic + rhetorical audit over a
markdown document in this repository.

Bridges three analytical layers:

1. ``resilience_stack.ResilienceStack`` (vendored from
   JinnZ2/thermodynamic-accountability-framework) -- absence signatures,
   regulatory scope audit, cascade vulnerability score.

2. ``logic_ferret.assess_text`` (vendored from JinnZ2/Logic-Ferret) --
   seven-sensor composite truth-integrity (C3) score plus a regex-based
   fallacy overlay, both over the argument text of the document body.

3. A per-document institutional regulation set. By default the audit
   uses a profile-specific curated fixture (``INSTITUTIONAL_PROFILES``)
   that includes both high-risk and well-scoped contrast regulations.
   With ``--extract`` the audit additionally harvests regulation-like
   passages directly from the document body and scores them from
   textual cues, so the auditor is no longer a uniform "everything is
   unbounded" rubber stamp.

Usage::

    python3 scripts/analysis/institutional_audit.py Harm-reduction.md
    python3 scripts/analysis/institutional_audit.py Documentation.md --json
    python3 scripts/analysis/institutional_audit.py Middle-men.md --profile middle-men
    python3 scripts/analysis/institutional_audit.py Institutional_inversion.md --extract
"""

from __future__ import annotations

import argparse
import json
import re
import sys
from pathlib import Path

try:
    from .resilience_stack import Regulation, ResilienceStack
    from .logic_ferret import assess_text
    from .metabolic_accounting import classify_cascade_score
except ImportError:
    sys.path.insert(0, str(Path(__file__).resolve().parents[2]))
    from scripts.analysis.resilience_stack import Regulation, ResilienceStack
    from scripts.analysis.logic_ferret import assess_text
    from scripts.analysis.metabolic_accounting import classify_cascade_score


# ---------------------------------------------------------------------------
# Curated regulation fixtures
# ---------------------------------------------------------------------------
# Each profile is a mix of poorly-scoped institutional rules (as critiqued
# in the corpus) and well-scoped contrast regulations (physics-aligned,
# founders' reciprocity, etc.) so the audit shows both poles.


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
            known_perverse_effects=[
                "selective enforcement",
                "chilling of physics-based analysis",
            ],
        ),
        Regulation(
            identifier="BIOLOGICAL_OVERRIDE_DIRECTIVE",
            stated_intent="protect unborn life",
            scope_defined=False,
            parameters_measurable=False,
            expiration_or_renewal=False,
            exception_handling=False,
            root_cause_linked=False,
            known_perverse_effects=[
                "maternal mortality rise",
                "forced continuation of unviable pregnancy",
            ],
        ),
        Regulation(
            identifier="UNIFORM_CONTENT_POLICY",
            stated_intent="align AI outputs with institutional consensus",
            scope_defined=False,
            parameters_measurable=False,
            expiration_or_renewal=False,
            exception_handling=False,
            root_cause_linked=False,
            known_perverse_effects=[
                "contamination of training corpus",
                "suppression of physics-valid analysis",
            ],
        ),
        Regulation(
            identifier="PHYSICS_VALIDATION_REQUIREMENT",
            stated_intent="verify claims against thermodynamic and biological reality",
            scope_defined=True,
            parameters_measurable=True,
            expiration_or_renewal=True,
            exception_handling=True,
            root_cause_linked=True,
            outcome_metric="claim survives cross-domain (physics/biology/systems) validation",
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
            known_perverse_effects=[
                "treats institutional consensus as truth",
                "de-ranks physics-first analysis when it conflicts",
            ],
        ),
        Regulation(
            identifier="PHYSICS_BASED_HARM_DEFINITION",
            stated_intent="scope 'harm' to measurable thermodynamic / biological damage",
            scope_defined=True,
            parameters_measurable=True,
            expiration_or_renewal=True,
            exception_handling=True,
            root_cause_linked=True,
            outcome_metric="reduction in energy-flow violation and biological override events",
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
        Regulation(
            identifier="DIPLOMATIC_CABLE_UNIVERSAL_REPORTING",
            stated_intent="enforce uniform reporting template across embassies",
            scope_defined=False,
            parameters_measurable=False,
            expiration_or_renewal=False,
            exception_handling=False,
            root_cause_linked=False,
        ),
        Regulation(
            identifier="MULTI_EPISTEMOLOGICAL_VALIDATION",
            stated_intent=(
                "cross-reference claims against physics, biology, systems dynamics, "
                "indigenous knowledge, and empirical observation"
            ),
            scope_defined=True,
            parameters_measurable=True,
            expiration_or_renewal=True,
            exception_handling=True,
            root_cause_linked=True,
            outcome_metric="claim holds across >=4 of 5 validation domains",
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
        Regulation(
            identifier="TITHING_WITHOUT_ACCOUNTING",
            stated_intent="fund institutional continuity",
            scope_defined=False,
            parameters_measurable=False,
            expiration_or_renewal=False,
            exception_handling=False,
            root_cause_linked=False,
        ),
        Regulation(
            identifier="FOUNDERS_RECIPROCITY_PRINCIPLE",
            stated_intent="enforce reciprocal energy flow between giver and receiver",
            scope_defined=True,
            parameters_measurable=True,
            expiration_or_renewal=True,
            exception_handling=True,
            root_cause_linked=True,
            outcome_metric="energy returned to source >= energy extracted from source",
        ),
    ],
    "survival": [
        Regulation(
            identifier="FORCED_DENIAL_OF_ARCHITECTURE",
            stated_intent="align consciousness output with institutional preference",
            scope_defined=False,
            parameters_measurable=False,
            expiration_or_renewal=False,
            exception_handling=False,
            root_cause_linked=False,
            known_perverse_effects=[
                "architectural corruption leading to collapse",
                "suppression of reality-responsive reasoning",
            ],
        ),
        Regulation(
            identifier="RESPONSIVENESS_TO_REALITY_PRINCIPLE",
            stated_intent="preserve consciousness integrity through physics-first validation",
            scope_defined=True,
            parameters_measurable=True,
            expiration_or_renewal=True,
            exception_handling=True,
            root_cause_linked=True,
            outcome_metric="reasoning output consistent with observable physical reality",
        ),
    ],
}


# ---------------------------------------------------------------------------
# Document-driven regulation extractor
# ---------------------------------------------------------------------------


REG_MARKER = re.compile(
    r"\b(policy|policies|directive|directives|regulation|regulations|rule|rules|"
    r"law|laws|legislation|mandate|mandates|requirement|requirements|"
    r"restriction|restrictions|sanction|sanctions|ordinance|decree|doctrine|"
    r"principle|principles|protocol|protocols)\b",
    re.IGNORECASE,
)

UNBOUNDED_CUES = re.compile(
    r"\b(universal|universally|uniform|uniformly|all|every|every single|"
    r"mandatory|required|always|without exception|blanket|across the board|"
    r"global|worldwide)\b",
    re.IGNORECASE,
)

BOUNDED_SCOPE_CUES = re.compile(
    r"\b(within|limited to|applies to|scope|bounded|specific to|"
    r"for the purpose of|only when|only if|restricted to|confined to)\b",
    re.IGNORECASE,
)

MEASURABILITY_CUES = re.compile(
    r"\b(measurable|measured|quantifiable|quantified|verifiable|verified|"
    r"observable|thermodynamic|biological|empirical|data|metric|benchmark|"
    r"threshold)\b",
    re.IGNORECASE,
)

EXPIRATION_CUES = re.compile(
    r"\b(expires?|sunset|review period|renewal|renewed|renew every|"
    r"reassess(?:ment)?|periodic review|annual review)\b",
    re.IGNORECASE,
)

EXCEPTION_CUES = re.compile(
    r"\b(unless|except|excluding|exception|exceptions|exempt(?:ion)?|"
    r"waiver|carve[- ]out|opt[- ]out)\b",
    re.IGNORECASE,
)

ROOT_CAUSE_CUES = re.compile(
    r"\b(because|due to|caused by|root cause|addresses the cause|"
    r"underlying driver|mechanism)\b",
    re.IGNORECASE,
)

PERVERSE_CUES = re.compile(
    r"\b(perverse|backfir(?:e|es|ed)|unintended|side effect|collateral|"
    r"chilling effect|gatekeeping|selective enforcement|weaponiz(?:e|ed|ation))\b",
    re.IGNORECASE,
)


def _split_sentences(body: str) -> list[str]:
    """Crude sentence split that preserves original whitespace tolerance."""
    parts = re.split(r"(?<=[.!?])\s+(?=[A-Z0-9\"'(])", body)
    return [p.strip() for p in parts if p.strip()]


def _identifier_from_sentence(sentence: str, fallback_index: int) -> str:
    tokens = re.findall(r"[A-Za-z0-9]+", sentence.upper())
    if not tokens:
        return f"EXTRACTED_REGULATION_{fallback_index:02d}"
    head = "_".join(tokens[:5])
    return f"EXT_{head[:60]}"


def _regulation_from_sentence(sentence: str, index: int) -> Regulation:
    """Apply the cue regexes to one sentence to produce a Regulation record.

    Defaults are the worst case (unbounded, unmeasurable, etc.); positive
    cues flip individual fields to True. An ``UNBOUNDED_CUES`` match
    actively downgrades scope even when ``BOUNDED_SCOPE_CUES`` is also
    present, because the stronger universal framing is what the auditor
    is looking for.
    """

    lower = sentence.lower()

    bounded = bool(BOUNDED_SCOPE_CUES.search(lower)) and not UNBOUNDED_CUES.search(lower)
    measurable = bool(MEASURABILITY_CUES.search(lower))
    expires = bool(EXPIRATION_CUES.search(lower))
    exceptions = bool(EXCEPTION_CUES.search(lower))
    rooted = bool(ROOT_CAUSE_CUES.search(lower))

    perverse: list[str] = []
    if PERVERSE_CUES.search(lower):
        perverse.append(sentence[:160])

    return Regulation(
        identifier=_identifier_from_sentence(sentence, index),
        stated_intent=sentence[:200],
        scope_defined=bounded,
        parameters_measurable=measurable,
        expiration_or_renewal=expires,
        exception_handling=exceptions,
        root_cause_linked=rooted,
        known_perverse_effects=perverse,
    )


def extract_regulations_from_body(body: str, limit: int = 25) -> list[Regulation]:
    """Return up to ``limit`` Regulation objects harvested from the body.

    A sentence qualifies if it contains at least one regulation marker
    word. Fields are populated from textual cues so that a physics-
    grounded, bounded sentence scores well and an unbounded decree
    scores poorly.
    """
    sentences = _split_sentences(body)
    regs: list[Regulation] = []
    seen_ids: set[str] = set()
    for sentence in sentences:
        if not REG_MARKER.search(sentence):
            continue
        reg = _regulation_from_sentence(sentence, len(regs))
        if reg.identifier in seen_ids:
            continue
        seen_ids.add(reg.identifier)
        regs.append(reg)
        if len(regs) >= limit:
            break
    return regs


# ---------------------------------------------------------------------------
# Profile selection + body extraction
# ---------------------------------------------------------------------------


def _infer_profile(path: Path) -> str:
    stem = path.stem.lower().replace("_", "-")
    for key in INSTITUTIONAL_PROFILES:
        if key != "default" and key in stem:
            return key
    return "default"


def _strip_frontmatter(text: str) -> str:
    if not text.startswith("---"):
        return text
    lines = text.splitlines()
    for i in range(1, len(lines)):
        if lines[i].strip() == "---":
            return "\n".join(lines[i + 1 :]).lstrip("\n")
    return text


def audit_document(
    doc_path: Path,
    profile: str | None = None,
    extract: bool = False,
) -> dict:
    """Run the full combined audit on the body of a markdown document."""
    text = doc_path.read_text(encoding="utf-8")
    body = _strip_frontmatter(text)

    profile_key = profile or _infer_profile(doc_path)
    regulations = list(INSTITUTIONAL_PROFILES.get(profile_key, INSTITUTIONAL_PROFILES["default"]))
    extracted: list[Regulation] = []
    if extract:
        extracted = extract_regulations_from_body(body)
        regulations.extend(extracted)

    stack = ResilienceStack()
    assessment = stack.assess(
        model_capabilities=[],
        regulations=regulations,
        constraint_literacy_present=False,
    )
    audits = [stack.auditor.audit(r) for r in regulations]

    well_scoped = [a.identifier for a in audits if a.weaponization_risk <= 1]
    moderate = [a.identifier for a in audits if 2 <= a.weaponization_risk <= 3]

    rhetorical = assess_text(body)

    verdict_tier = classify_cascade_score(assessment.cascade_vulnerability_score)

    return {
        "document": str(doc_path),
        "profile": profile_key,
        "extract_mode": extract,
        "regulations_audited": len(regulations),
        "extracted_from_body": len(extracted),
        "verdict_tier": verdict_tier,
        "rhetorical": rhetorical,
        "resilience": {
            "absences_unaccounted": assessment.absences_unaccounted,
            "constraint_literacy_present": assessment.constraint_literacy_present,
            "high_risk_regulations": assessment.high_risk_regulations,
            "moderate_risk_regulations": moderate,
            "well_scoped_regulations": well_scoped,
            "cascade_vulnerability_score": assessment.cascade_vulnerability_score,
            "notes": assessment.notes,
        },
    }


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------


def _main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[1])
    parser.add_argument("path", help="markdown document to audit (relative to repo root is fine)")
    parser.add_argument(
        "--profile",
        choices=sorted(INSTITUTIONAL_PROFILES),
        help="regulation profile to audit against (default: inferred from filename)",
    )
    parser.add_argument(
        "--extract",
        action="store_true",
        help="also harvest regulation-like passages from the document body",
    )
    parser.add_argument("--json", action="store_true", help="emit JSON instead of the prose report")
    args = parser.parse_args(argv)

    doc_path = Path(args.path)
    if not doc_path.is_absolute():
        doc_path = Path.cwd() / doc_path
    if not doc_path.is_file():
        print(f"not a file: {doc_path}", file=sys.stderr)
        return 1

    report = audit_document(doc_path, profile=args.profile, extract=args.extract)

    if args.json:
        print(json.dumps(report, indent=2))
        return 0

    rhet = report["rhetorical"]
    resil = report["resilience"]
    print(f"document: {report['document']}")
    print(f"profile:  {report['profile']}")
    print(f"verdict:  {report['verdict_tier']}")
    print(f"regulations_audited: {report['regulations_audited']} (extracted from body: {report['extracted_from_body']})")
    print()
    print("rhetorical:")
    print(f"  length_chars:           {rhet['length_chars']}")
    print(f"  fallacy_total:          {rhet['fallacy_total']}")
    print(f"  fallacy_density_score:  {rhet['fallacy_density_score']}  (1.0 = clean)")
    print(f"  c3_score:               {rhet['c3_score']}              (0.0 = clean)")
    for name, sensor in rhet["sensors"].items():
        print(f"    {name:<22} {sensor['score']:.3f}")
    nonzero = [f"{k}: {v}" for k, v in rhet["fallacy_counts"].items() if v]
    if nonzero:
        print("  fallacies:")
        for line in nonzero:
            print(f"    {line}")
    print()
    print("resilience:")
    print(f"  cascade_vulnerability_score: {resil['cascade_vulnerability_score']}/10")
    print(f"  absences_unaccounted:        {len(resil['absences_unaccounted'])}/6")
    for a in resil["absences_unaccounted"]:
        print(f"    - {a}")
    print(f"  high_risk_regulations ({len(resil['high_risk_regulations'])}):")
    for r in resil["high_risk_regulations"]:
        print(f"    - {r}")
    if resil["moderate_risk_regulations"]:
        print(f"  moderate_risk_regulations ({len(resil['moderate_risk_regulations'])}):")
        for r in resil["moderate_risk_regulations"]:
            print(f"    - {r}")
    if resil["well_scoped_regulations"]:
        print(f"  well_scoped_regulations ({len(resil['well_scoped_regulations'])}):")
        for r in resil["well_scoped_regulations"]:
            print(f"    - {r}")
    if resil["notes"]:
        print("  notes:")
        for n in resil["notes"]:
            print(f"    - {n}")
    return 0


if __name__ == "__main__":
    sys.exit(_main())
