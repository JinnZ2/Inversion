#!/usr/bin/env python3
"""
Scope Check -- Carrier Audit for Belief / Claim / Signal Models

Operationalizes the scope_carrier_invariance principle documented in
Scope-collapse.md: claims about epistemic dynamics are valid only within
the carrier representation used to model belief; results obtained in
binary belief models describe the behavior of binary belief models.

Given a text (a study abstract, a policy document, a model description,
a claim), the scope check looks for:

  1. Binary-projection signatures   -- A vs B / true vs false / xor framings
  2. Scope-conditionals             -- "within", "boundary conditions",
                                       "regime", "holds when"
  3. Frame-translation language     -- "shared substrate", "third structure",
                                       "reframing", "across frames"
  4. Verb-relational observation    -- "when X flows", relational language
                                       describing constraint shape
  5. Substrate-state observation    -- "substrate", "manifold",
                                       "field", "state" as observation
  6. Trajectory / time-derivative   -- "trajectory", "rate of change",
                                       "conditional on time"

A text that scores high on (1) and low on (2)-(6) is exhibiting carrier
collapse: the binary projection has been performed but the signals that
would let the system see the projection are absent. Such a text's
internal results are valid; its external claims are out of scope.

Anchored on:
  Stein, Cruz, Grossi, Testori (2026). Free Information Disrupts Even
  Bayesian Crowds. PNAS 123(14): e2518472123.

Exports the structured principle so other modules (first_principles_audit,
playground, logic_ferret consumers) can consume it programmatically.
"""

from __future__ import annotations

import argparse
import json
import re
import sys
from dataclasses import asdict, dataclass, field
from typing import Any


# ---------------------------------------------------------------------------
# Structured principle data (programmatic export)
# ---------------------------------------------------------------------------


PRINCIPLE: dict[str, str] = {
    "name": "scope_carrier_invariance",
    "statement": (
        "Any claim about epistemic dynamics is valid only within the "
        "carrier representation used to model belief. Claims do not "
        "transfer across representations without showing that the "
        "structure being claimed about is preserved by the projection."
    ),
    "binary_carrier_corollary": (
        "Results obtained in binary belief models describe the behavior "
        "of binary belief models. They are not automatically claims about "
        "minds, communities, or communication systems whose native "
        "representation is richer."
    ),
    "test_for_misuse": (
        "If a policy derived from a binary-carrier study would act on "
        "agents whose cognition is non-binary, the policy is operating "
        "outside the study's scope and any harm it causes is on the "
        "policy, not on the study."
    ),
}


BINARY_BLIND_SPOTS: dict[str, str] = {
    "frame_translation": (
        "The move that breaks homophily in a real network is rarely "
        "'switching from A to B' -- it is 'reframing A and B in a shared "
        "substrate where both are partial views of a third structure.' "
        "The binary model has no representation for this; the agent who "
        "does it looks identical to a flipper or a noise source."
    ),
    "scope_conditional_truth": (
        "Claim X may be true at Holocene boundary conditions and invalid "
        "at Anthropocene ones. Binary agents have no slot for 'true within "
        "scope, false outside'; they collapse it to a global vote."
    ),
    "multi_frame_holders": (
        "Tradition-carriers, cross-domain synthesizers, and load-bearing "
        "operators hold multiple simultaneous frames. Their belief vector "
        "is not one bit; it is a manifold. The binary model has no axis "
        "to register them."
    ),
    "verb_relational_evidence": (
        "Many real claims encode relations, not propositions. 'When X flows "
        "into Y under condition Z, the substrate reorganizes' is not A or B; "
        "it is a constraint shape. A binary aggregator rounds it to whichever "
        "pole it is closest to and discards the shape."
    ),
    "substrate_primary_observation": (
        "Indigenous generative knowledge often reports substrate state, not "
        "propositional claims. Song-as-landscape-document is closer to a "
        "sensor reading than a vote. Binary models cannot consume it."
    ),
    "temporal_truth": (
        "Many real claims are 'true on this trajectory, conditional on the "
        "current rate of change.' The binary model has no time-derivative "
        "axis."
    ),
}


BINARY_AS_HOMOPHILY: dict[str, str] = {
    "before_any_pairing": (
        "Every observation has been mapped to {A, B}. The manifold is gone. "
        "The verbs are gone. The scope conditions are gone."
    ),
    "this_is_where_correlation_was_introduced": (
        "Any two agents who saw the same substrate event now hold identical "
        "bits because the projection is lossy and one-dimensional. They "
        "would have held different verb-relational descriptions; the "
        "projection erased the difference."
    ),
    "result": (
        "The homophily detected in the pairing graph was already injected "
        "by the observation-to-bit operator. The pairing only amplifies "
        "correlation that the encoding created."
    ),
}


HONEST_RESTATEMENT: str = (
    "Within a binary truth model, with binary belief states, under "
    "homophilous pairing, increased honest exchange reduces the fraction "
    "of agents holding the bit that matches the pre-declared correct bit. "
    "This is a real and useful finding about binary systems. It is not a "
    "finding about epistemics, communication, or whether information "
    "should flow."
)


REFERENCE: dict[str, str] = {
    "citation": (
        "Stein, Cruz, Grossi, Testori (2026). Free Information Disrupts "
        "Even Bayesian Crowds. PNAS 123(14): e2518472123."
    ),
    "doi": "10.1073/pnas.2518472123",
}


# ---------------------------------------------------------------------------
# Detection patterns
# ---------------------------------------------------------------------------


_BINARY_PATTERNS: list[tuple[str, str]] = [
    ("a_vs_b", r"\b[A-Z]\s+vs\.?\s+[A-Z]\b"),
    ("a_xor_b", r"\b(xor|exclusive\s+or|either[-\s]or)\b"),
    ("true_vs_false", r"\b(true\s+(?:vs\.?|or)\s+false|correct\s+vs\.?\s+incorrect)\b"),
    ("binary_choice", r"\bbinary\s+(?:choice|state|belief|truth|model|variable|outcome)s?\b"),
    ("two_options", r"\b(?:one\s+of\s+two|two\s+options|dichotom(?:y|ous)|polar(?:ized|ization))\b"),
    ("bit_state", r"\b(?:bit|0\s*/\s*1|0\s+or\s+1|yes\s*/\s*no)\b"),
    ("forced_pick", r"\b(?:pick(?:s|ed)?\s+(?:one|the\s+correct))\b"),
]


_SCOPE_CONDITIONAL_PATTERNS: list[tuple[str, str]] = [
    ("within_scope", r"\bwithin\s+(?:the\s+)?(?:scope|frame|regime|context|model)\b"),
    ("boundary_conditions", r"\bboundary\s+conditions?\b"),
    ("regime", r"\b(?:regime|regime[-\s]conditional)\b"),
    ("holds_when", r"\b(?:holds?|valid|true)\s+(?:when|under|within|for)\b"),
    ("breaks_outside", r"\b(?:breaks?|fails?|invalid)\s+(?:outside|across|beyond)\b"),
    ("conditional_on", r"\bconditional\s+on\b"),
    ("scope_dependent", r"\bscope[-\s]dependent\b"),
]


_FRAME_TRANSLATION_PATTERNS: list[tuple[str, str]] = [
    ("shared_substrate", r"\bshared\s+(?:substrate|frame|representation)\b"),
    ("third_structure", r"\bthird\s+(?:structure|frame|view)\b"),
    ("reframing", r"\b(?:reframing|reframe|frame[-\s]shifting|frame[-\s]translation)\b"),
    ("partial_view", r"\bpartial\s+view(?:s)?\s+of\b"),
    ("across_frames", r"\bacross\s+(?:frames|representations|carriers|domains)\b"),
    ("translate_between", r"\btranslat(?:e|ing|ion)\s+between\b"),
]


_VERB_RELATIONAL_PATTERNS: list[tuple[str, str]] = [
    ("when_x_flows", r"\bwhen\s+\w+\s+(?:flows?|moves?|enters?|leaves?|couples?)\b"),
    ("relation_under", r"\bunder\s+(?:condition|constraint|coupling)\b"),
    ("constraint_shape", r"\bconstraint\s+(?:shape|surface|geometry)\b"),
    ("relational", r"\b(?:relational|verb[-\s]first|verb[-\s]relational)\b"),
    ("flows_into", r"\bflows?\s+into\b"),
]


_SUBSTRATE_STATE_PATTERNS: list[tuple[str, str]] = [
    ("substrate", r"\bsubstrate(?:\s+state)?\b"),
    ("manifold", r"\bmanifold\b"),
    ("field_state", r"\bfield(?:\s+state)?\b"),
    ("sensor_reading", r"\bsensor(?:\s+reading|\s+state)?\b"),
    ("landscape_doc", r"\b(?:landscape|territory)\s+(?:document|reading|state)\b"),
    ("substrate_observation", r"\bsubstrate[-\s]state\s+observation\b"),
]


_TRAJECTORY_PATTERNS: list[tuple[str, str]] = [
    ("trajectory", r"\btrajector(?:y|ies)\b"),
    ("rate_of_change", r"\brate\s+of\s+change\b"),
    ("time_derivative", r"\btime[-\s]derivative\b"),
    ("on_this_path", r"\bon\s+(?:this|the\s+current)\s+(?:trajectory|path)\b"),
    ("conditional_on_time", r"\bconditional\s+on\s+(?:time|rate|change)\b"),
    ("trending_toward", r"\btrending\s+(?:toward|away)\b"),
]


_AXES: dict[str, list[tuple[str, str]]] = {
    "binary_projection": _BINARY_PATTERNS,
    "scope_conditional": _SCOPE_CONDITIONAL_PATTERNS,
    "frame_translation": _FRAME_TRANSLATION_PATTERNS,
    "verb_relational": _VERB_RELATIONAL_PATTERNS,
    "substrate_state": _SUBSTRATE_STATE_PATTERNS,
    "trajectory": _TRAJECTORY_PATTERNS,
}


# ---------------------------------------------------------------------------
# Report types
# ---------------------------------------------------------------------------


@dataclass
class AxisHits:
    axis: str
    matches: dict[str, int] = field(default_factory=dict)
    total: int = 0

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass
class ScopeReport:
    """Result of a scope/carrier audit on a text."""

    source: str
    text_length_chars: int
    axes: dict[str, AxisHits]
    binary_score: float
    richness_score: float
    carrier_collapse_score: float
    verdict: str
    findings: list[str] = field(default_factory=list)

    def to_dict(self) -> dict[str, Any]:
        return {
            "source": self.source,
            "text_length_chars": self.text_length_chars,
            "axes": {k: v.to_dict() for k, v in self.axes.items()},
            "binary_score": round(self.binary_score, 3),
            "richness_score": round(self.richness_score, 3),
            "carrier_collapse_score": round(self.carrier_collapse_score, 3),
            "verdict": self.verdict,
            "findings": self.findings,
        }


# ---------------------------------------------------------------------------
# Detection
# ---------------------------------------------------------------------------


def _count_axis(text: str, patterns: list[tuple[str, str]]) -> AxisHits:
    matches: dict[str, int] = {}
    for name, pattern in patterns:
        hits = len(re.findall(pattern, text, flags=re.IGNORECASE))
        if hits:
            matches[name] = hits
    total = sum(matches.values())
    return AxisHits(axis="", matches=matches, total=total)


_RICHNESS_AXES: tuple[str, ...] = (
    "scope_conditional",
    "frame_translation",
    "verb_relational",
    "substrate_state",
    "trajectory",
)


def analyze(text: str, source: str = "<stdin>") -> ScopeReport:
    """Run the scope/carrier audit on a text."""
    axes: dict[str, AxisHits] = {}
    for axis_name, patterns in _AXES.items():
        hits = _count_axis(text, patterns)
        hits.axis = axis_name
        axes[axis_name] = hits

    binary_total = axes["binary_projection"].total
    richness_total = sum(axes[a].total for a in _RICHNESS_AXES)
    denom = binary_total + richness_total

    if denom == 0:
        binary_score = 0.0
        richness_score = 0.0
        carrier_collapse_score = 0.0
    else:
        binary_score = binary_total / denom
        richness_score = richness_total / denom
        # Carrier collapse: high binary signal AND low richness across axes.
        # Penalize each missing richness axis.
        missing_axes = sum(1 for a in _RICHNESS_AXES if axes[a].total == 0)
        missing_fraction = missing_axes / len(_RICHNESS_AXES)
        carrier_collapse_score = binary_score * (0.5 + 0.5 * missing_fraction)

    findings: list[str] = []
    if binary_total > 0:
        findings.append(
            f"binary-projection signatures detected: {binary_total} "
            f"hit(s) across {len(axes['binary_projection'].matches)} pattern(s)"
        )
    for axis_name in _RICHNESS_AXES:
        if axes[axis_name].total == 0:
            findings.append(
                f"axis '{axis_name}' has no signal; the carrier may be "
                "unable to represent this structure"
            )

    if carrier_collapse_score >= 0.6:
        verdict = (
            "CARRIER COLLAPSE: binary projection dominant and richness axes "
            "largely absent. Internal results may be valid; external claims "
            "are out of scope without re-projection."
        )
    elif carrier_collapse_score >= 0.3:
        verdict = (
            "PARTIAL CARRIER COLLAPSE: binary signal present but some "
            "richness axes are populated. Check whether the conclusions "
            "rely on the binary projection."
        )
    elif binary_total > 0 and richness_total >= binary_total:
        verdict = (
            "MIXED CARRIER: binary and richer representations both "
            "present. Verify the conclusions are stated within the "
            "carrier they were derived in."
        )
    elif binary_total == 0 and richness_total == 0:
        verdict = (
            "NO SIGNAL: text too short or too generic for carrier inference."
        )
    else:
        verdict = (
            "RICH CARRIER: scope conditionals, frame translation, "
            "substrate-state, or trajectory language present. Carrier "
            "appears to support non-binary structure."
        )

    return ScopeReport(
        source=source,
        text_length_chars=len(text),
        axes=axes,
        binary_score=binary_score,
        richness_score=richness_score,
        carrier_collapse_score=carrier_collapse_score,
        verdict=verdict,
        findings=findings,
    )


# ---------------------------------------------------------------------------
# Programmatic export
# ---------------------------------------------------------------------------


def scope_check_principle() -> dict[str, Any]:
    """Return the structured scope_carrier_invariance principle.

    Used by other modules (first_principles_audit, the playground) that
    want to embed the principle without reading the markdown doc.
    """
    return {
        "principle": dict(PRINCIPLE),
        "binary_blind_spots": dict(BINARY_BLIND_SPOTS),
        "binary_as_homophily": dict(BINARY_AS_HOMOPHILY),
        "honest_restatement": HONEST_RESTATEMENT,
        "reference": dict(REFERENCE),
    }


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------


def _print_report(report: ScopeReport) -> None:
    print(f"source:                  {report.source}")
    print(f"length (chars):          {report.text_length_chars}")
    print(f"binary_score:            {report.binary_score:.3f}")
    print(f"richness_score:          {report.richness_score:.3f}")
    print(f"carrier_collapse_score:  {report.carrier_collapse_score:.3f}")
    print()
    for axis_name, hits in report.axes.items():
        if hits.total:
            print(f"{axis_name}: {hits.total} hit(s) -> {hits.matches}")
        else:
            print(f"{axis_name}: 0 hits")
    print()
    if report.findings:
        print("findings:")
        for f in report.findings:
            print(f"  - {f}")
    print()
    print(f"VERDICT: {report.verdict}")


def main() -> None:
    parser = argparse.ArgumentParser(
        description=(
            "Scope/carrier audit. Detects binary-projection signatures and "
            "the absence of scope-conditional, frame-translation, "
            "verb-relational, substrate-state, and trajectory language "
            "that would let a richer carrier be visible. Anchored on "
            "Stein, Cruz, Grossi, Testori (2026), DOI 10.1073/pnas.2518472123."
        ),
    )
    parser.add_argument("file", nargs="?", help="path to a text/markdown file")
    parser.add_argument("--text", "-t", help="inline text to audit")
    parser.add_argument(
        "--principle", action="store_true",
        help="print the structured scope_carrier_invariance principle and exit",
    )
    parser.add_argument("--json", action="store_true", help="output JSON")
    args = parser.parse_args()

    if args.principle:
        print(json.dumps(scope_check_principle(), indent=2))
        return

    if args.text:
        text = args.text
        source = "<inline>"
    elif args.file:
        with open(args.file) as f:
            text = f.read()
        source = args.file
    else:
        text = sys.stdin.read()
        source = "<stdin>"

    report = analyze(text, source=source)
    if args.json:
        print(json.dumps(report.to_dict(), indent=2))
    else:
        _print_report(report)


if __name__ == "__main__":
    main()
