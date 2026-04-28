#!/usr/bin/env python3
"""
Biological Mismatch -- Regime Check for Organisms Forced into Contradictory Environments

Distinguishes regime mismatch from pathology. When a behavior is adaptive in
regime A but is being deployed/forced/measured in regime B, the behavior is
not a defect of the organism -- it is a mismatch with the environment.

Standard frame:                       Biological mismatch frame:
  observe behavior X                    observe behavior X in environment Y
  -> diagnose as defect                 -> check: is X adaptive in any regime?
  -> prescribe fix                      -> if YES: is Y that regime?
  -> blame organism                     -> if NO: regime mismatch flagged
                                        -> environment is the constraint

Each regime entry documents the underlying biology, the environments where
the regime is adaptive, the environments where it is mismatched, the
signatures of mismatch, and the misdiagnoses commonly applied when the
environment-as-constraint is not interrogated.

This is a minimal first pass: regime library, behavior/environment matcher,
and a CLI. Audit wrapper and demo cases are deferred to a follow-up.

References:
  - Eide & Eide (2011): The Dyslexic Advantage
  - Graeber & Wengrow (2021): The Dawn of Everything
  - Feldman (2015): fatherhood neurobiology
  - documented continuity of distributed governance and nomadic baselines
    across Indigenous and pre-state societies
"""

from __future__ import annotations

import argparse
import json
import sys
from dataclasses import asdict, dataclass, field
from enum import Enum
from typing import Any


# ---------------------------------------------------------------------------
# Regime profiles
# ---------------------------------------------------------------------------


class RegimeCategory(Enum):
    NEUROCOGNITIVE = "neurocognitive"
    METABOLIC = "metabolic"
    HORMONAL = "hormonal"
    SOCIAL_STRUCTURAL = "social_structural"
    SENSORY = "sensory"
    REPRODUCTIVE = "reproductive"
    DEVELOPMENTAL = "developmental"


@dataclass
class BiologicalRegime:
    """A baseline biological/cognitive profile and the environments it was shaped by."""

    id: str
    name: str
    category: RegimeCategory
    description: str
    traits: list[str] = field(default_factory=list)
    adaptive_in_environments: list[str] = field(default_factory=list)
    mismatch_environments: list[str] = field(default_factory=list)
    mismatch_signatures: list[str] = field(default_factory=list)
    common_misdiagnoses: list[str] = field(default_factory=list)
    evidence_sources: list[str] = field(default_factory=list)

    def to_dict(self) -> dict[str, Any]:
        d = asdict(self)
        d["category"] = self.category.value
        return d


REGIMES: dict[str, BiologicalRegime] = {
    "dyslexic_spatial": BiologicalRegime(
        id="dyslexic_spatial",
        name="dyslexic spatial-kinetic processing",
        category=RegimeCategory.NEUROCOGNITIVE,
        description=(
            "Visual-spatial reasoning prioritized over linear text decoding. "
            "Pattern recognition across 3D, kinetic, and systems-level inputs."
        ),
        traits=[
            "non-linear text processing",
            "high spatial reasoning capability",
            "kinetic/embodied learning preference",
            "systems-level pattern recognition",
            "visual problem-solving",
            "real-time mechanical intuition",
        ],
        adaptive_in_environments=[
            "hands-on mechanical work",
            "navigation and spatial problem solving",
            "construction and building",
            "real-time emergency response",
            "ecological pattern recognition",
            "complex 3D systems (engines, terrain, structures)",
        ],
        mismatch_environments=[
            "text-heavy bureaucratic work",
            "standardized testing environments",
            "linear text-based education",
            "credential-gated institutional careers",
            "speed-reading-required roles",
        ],
        mismatch_signatures=[
            "slow text processing speed",
            "frustration with paperwork",
            "low test scores despite high capability",
            "appearing 'stupid' in written contexts",
            "exhaustion from text-based work",
        ],
        common_misdiagnoses=[
            "learning disabled",
            "low intelligence",
            "lazy / unmotivated",
            "needs to try harder",
        ],
        evidence_sources=[
            "Eide & Eide, The Dyslexic Advantage (2011)",
            "Schneps et al., visual processing studies, MIT",
            "documented overrepresentation in engineering, art, mechanical fields",
        ],
    ),
    "high_throughput_nervous_system": BiologicalRegime(
        id="high_throughput_nervous_system",
        name="high baseline energy / endurance regime",
        category=RegimeCategory.METABOLIC,
        description=(
            "Higher than typical baseline energy throughput. Stress regulation "
            "through motion and continuous engagement rather than rest."
        ),
        traits=[
            "high mitochondrial efficiency",
            "stress regulation through motion",
            "continuous engagement preference",
            "low fatigue at standard work loads",
            "cognitive function maintained at extended hours",
        ],
        adaptive_in_environments=[
            "long-haul physical work",
            "endurance athletics",
            "multi-domain problem solving",
            "extended attention tasks",
            "frontier and constraint-rich environments",
        ],
        mismatch_environments=[
            "8-hour sedentary office work",
            "standardized work-rest cycles",
            "environments forbidding parallel task execution",
            "rest-as-virtue cultural frames",
        ],
        mismatch_signatures=[
            "restlessness in standard work environments",
            "appearing 'workaholic' or 'unable to rest'",
            "boredom in single-domain tasks",
            "needs higher stimulation than peers",
        ],
        common_misdiagnoses=[
            "ADHD without context",
            "anxiety disorder",
            "burnout-prone (when actually under-utilized)",
            "unable to relax / unhealthy",
        ],
        evidence_sources=[
            "individual variation in metabolic baseline (well-documented)",
            "endurance athlete physiology research",
            "chronotype and circadian variation literature",
        ],
    ),
    "distributed_decision_baseline": BiologicalRegime(
        id="distributed_decision_baseline",
        name="distributed/consensus decision-making baseline",
        category=RegimeCategory.SOCIAL_STRUCTURAL,
        description=(
            "Neurobiology calibrated for distributed authority, consensus building, "
            "council-based decisions. Sustained for thousands of years in many "
            "Indigenous and pre-state societies."
        ),
        traits=[
            "high attunement to group state",
            "consensus-seeking neural patterns",
            "resistance to unilateral authority",
            "patience with deliberation",
            "discomfort with rigid hierarchy",
        ],
        adaptive_in_environments=[
            "council-based governance",
            "small-to-medium community decisions",
            "cooperative work structures",
            "multi-generational knowledge integration",
            "consensus-based conflict resolution",
        ],
        mismatch_environments=[
            "corporate top-down hierarchy",
            "military command structure",
            "industrial wage-labor relationships",
            "majority-rule electoral systems",
            "authoritarian institutional frames",
        ],
        mismatch_signatures=[
            "questioning authority directives",
            "slow compliance with unilateral orders",
            "coalition-building when system expects individual compliance",
            "resistance interpreted as defiance",
        ],
        common_misdiagnoses=[
            "rebellious / oppositional",
            "uncooperative",
            "lacks leadership (when actually distributing it)",
            "anti-authority disorder",
        ],
        evidence_sources=[
            "Haudenosaunee Confederacy governance documentation",
            "Graeber & Wengrow, The Dawn of Everything (2021)",
            "documented continuity of consensus governance across continents",
        ],
    ),
    "care_capacity_masculine": BiologicalRegime(
        id="care_capacity_masculine",
        name="care-capable masculine baseline",
        category=RegimeCategory.REPRODUCTIVE,
        description=(
            "Male biology with strong nurturing, teaching, and child-care neural "
            "pathways. Documented as a desired masculine trait in many tribal and "
            "pre-state societies; pathologized in property-extraction frames."
        ),
        traits=[
            "high nurturing response to children",
            "teaching/mentoring inclination",
            "emotional attunement to family/community",
            "patience with multi-year child development",
            "child-presence preference over status-display",
        ],
        adaptive_in_environments=[
            "extended-family child rearing",
            "tribal mentorship structures",
            "communities valuing fatherhood-as-presence",
            "small-scale cooperative economies",
        ],
        mismatch_environments=[
            "industrial wage-labor (father-as-absent-provider)",
            "corporate masculinity frames",
            "status-via-economic-dominance cultures",
            "hyper-competitive male peer groups",
        ],
        mismatch_signatures=[
            "preferring time with children to status competition",
            "low motivation for status-display work",
            "reading as 'soft' in dominant culture",
            "career disadvantage in extraction-frame workplaces",
        ],
        common_misdiagnoses=[
            "lacking ambition",
            "unmasculine / weak",
            "underperforming (in extraction-frame metrics)",
            "depression (when actually constraint mismatch)",
        ],
        evidence_sources=[
            "ethnographic documentation across tribal societies",
            "fatherhood neuroscience (Feldman, Abraham et al.)",
            "Indigenous oral knowledge across Americas, Pacific, Africa",
        ],
    ),
    "environmental_attunement": BiologicalRegime(
        id="environmental_attunement",
        name="high environmental sensory attunement",
        category=RegimeCategory.SENSORY,
        description=(
            "Heightened perception of weather, ecological, magnetic, animal, and "
            "plant signals. Calibrated by generations of constraint-integrated "
            "living. Often called 'intuition' when it is actually data integration."
        ),
        traits=[
            "weather/pressure change detection",
            "animal behavior pattern reading",
            "plant/seasonal cycle attunement",
            "magnetic/directional sensitivity",
            "early warning detection (subtle environmental shifts)",
        ],
        adaptive_in_environments=[
            "wilderness travel and hunting",
            "ecological stewardship",
            "agricultural decision-making",
            "navigation without instruments",
            "climate-coupled survival contexts",
        ],
        mismatch_environments=[
            "indoor sedentary work",
            "climate-controlled isolation",
            "screen-mediated reality",
            "urban sensory-flattening environments",
        ],
        mismatch_signatures=[
            "discomfort indoors / under fluorescent light",
            "stress in disconnected environments",
            "sensitivity called 'too much' by neurotypical peers",
            "getting 'feelings' about things that prove correct",
        ],
        common_misdiagnoses=[
            "overly sensitive / HSP without context",
            "anxious / hypervigilant",
            "superstitious / unscientific",
            "needs to toughen up",
        ],
        evidence_sources=[
            "Indigenous tracking and navigation literature",
            "biometeorology and human pressure sensitivity research",
            "documented predictive accuracy of place-based knowledge holders",
        ],
    ),
    "nomadic_constraint_integration": BiologicalRegime(
        id="nomadic_constraint_integration",
        name="nomadic / mobile constraint-adaptive baseline",
        category=RegimeCategory.METABOLIC,
        description=(
            "Neurobiology shaped by mobility, seasonal adaptation, multi-domain "
            "problem-solving across changing environments. Documented across "
            "continents in nomadic and semi-nomadic lineages."
        ),
        traits=[
            "rapid environmental recalibration",
            "multi-domain skill maintenance",
            "low attachment to fixed structures",
            "high navigational and orientation capability",
            "resourcefulness across changing constraint sets",
        ],
        adaptive_in_environments=[
            "mobile work (driving, trading, nomadic herding)",
            "frontier and exploration contexts",
            "multi-environment field work",
            "constraint-rich problem solving",
        ],
        mismatch_environments=[
            "single-location career paths",
            "settled bureaucratic structures",
            "credentialed-specialist career frames",
            "fixed-asset wealth accumulation cultures",
        ],
        mismatch_signatures=[
            "career-path discomfort",
            "reading as 'not committed' or 'drifter'",
            "resistance to single-domain specialization",
            "discomfort with sedentary expectations",
        ],
        common_misdiagnoses=[
            "lacks discipline / can't commit",
            "underachiever",
            "antisocial / loner",
            "unstable",
        ],
        evidence_sources=[
            "ethnographic documentation of nomadic societies",
            "trucking and mobile-work culture studies",
            "DRD4-7R allele research and novelty-seeking baseline",
        ],
    ),
}


# ---------------------------------------------------------------------------
# Mismatch detection
# ---------------------------------------------------------------------------


@dataclass
class MismatchReport:
    behavior_or_trait: str
    environment: str
    matching_regimes: list[str]
    is_adaptive_somewhere: bool
    is_adaptive_in_current_environment: bool
    likely_misdiagnoses: list[str]
    actual_constraint: str
    recommendation: str

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


_STOPWORDS = {
    "with", "from", "into", "that", "this", "than", "when", "then", "what",
    "their", "your", "have", "been", "they", "them", "ones", "where", "while",
    "could", "would", "should", "about", "across", "actual", "called", "really",
}


def _keyword_match(phrase: str, target: str) -> bool:
    """Coarse keyword overlap. At least half of the meaningful words from
    the phrase must appear in the target."""
    phrase_lower = phrase.lower()
    target_lower = target.lower()
    for ch in ".,;:()/'\"":
        phrase_lower = phrase_lower.replace(ch, " ")
        target_lower = target_lower.replace(ch, " ")
    phrase_words = {
        w for w in phrase_lower.split() if len(w) > 3 and w not in _STOPWORDS
    }
    target_words = {w for w in target_lower.split() if len(w) > 3}
    if not phrase_words:
        return False
    overlap = phrase_words & target_words
    return len(overlap) >= max(1, (len(phrase_words) + 1) // 2)


def check_behavior(
    behavior_description: str, environment_description: str
) -> MismatchReport:
    """Identify regimes where the behavior is adaptive, check whether the
    current environment matches, and surface likely misdiagnoses."""
    behavior_lower = behavior_description.lower()
    env_lower = environment_description.lower()

    scored: list[tuple[int, str]] = []
    for regime_id, regime in REGIMES.items():
        score = 0
        for signal in regime.traits + regime.mismatch_signatures:
            if _keyword_match(signal, behavior_lower):
                score += 1
        if score > 0:
            scored.append((score, regime_id))

    scored.sort(reverse=True)
    matching: list[str] = []
    if scored:
        top_score = scored[0][0]
        matching = [rid for s, rid in scored if s >= max(top_score, 1)]

    if not matching:
        return MismatchReport(
            behavior_or_trait=behavior_description,
            environment=environment_description,
            matching_regimes=[],
            is_adaptive_somewhere=False,
            is_adaptive_in_current_environment=False,
            likely_misdiagnoses=[],
            actual_constraint=(
                "no documented regime matched; expand library or verify the "
                "behavior is genuinely maladaptive"
            ),
            recommendation=(
                "DO NOT pathologize without further investigation. Library is "
                "not exhaustive; add new regime if needed."
            ),
        )

    adaptive_now = False
    misdiagnoses: set[str] = set()
    for regime_id in matching:
        regime = REGIMES[regime_id]
        if any(_keyword_match(e, env_lower) for e in regime.adaptive_in_environments):
            adaptive_now = True
        if any(_keyword_match(e, env_lower) for e in regime.mismatch_environments):
            misdiagnoses.update(regime.common_misdiagnoses)

    if adaptive_now:
        return MismatchReport(
            behavior_or_trait=behavior_description,
            environment=environment_description,
            matching_regimes=matching,
            is_adaptive_somewhere=True,
            is_adaptive_in_current_environment=True,
            likely_misdiagnoses=[],
            actual_constraint=(
                "behavior is adaptive in current environment; no mismatch detected"
            ),
            recommendation="RECOGNIZE: this is functioning as designed. Do not pathologize.",
        )

    return MismatchReport(
        behavior_or_trait=behavior_description,
        environment=environment_description,
        matching_regimes=matching,
        is_adaptive_somewhere=True,
        is_adaptive_in_current_environment=False,
        likely_misdiagnoses=sorted(misdiagnoses),
        actual_constraint=(
            f"behavior is adaptive in regimes {matching} but current environment "
            f"is mismatched. The environment is the constraint, not the organism."
        ),
        recommendation=(
            "DO NOT PATHOLOGIZE. The pine tree is not failing to be an oak. "
            "Either change the environment to match the regime, or recognize "
            "that you are forcing incompatible biology into an incompatible frame."
        ),
    )


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------


def _print_regime_list() -> None:
    for regime in REGIMES.values():
        print(f"{regime.id}  [{regime.category.value}]")
        print(f"    {regime.name}")


def _print_report(report: MismatchReport) -> None:
    print(f"behavior:           {report.behavior_or_trait}")
    print(f"environment:        {report.environment}")
    print(f"matching regimes:   {report.matching_regimes}")
    print(f"adaptive somewhere: {report.is_adaptive_somewhere}")
    print(f"adaptive HERE:      {report.is_adaptive_in_current_environment}")
    if report.likely_misdiagnoses:
        print(f"likely misdiagnoses: {report.likely_misdiagnoses}")
    print(f"actual constraint:  {report.actual_constraint}")
    print(f"recommendation:     {report.recommendation}")


def main() -> None:
    parser = argparse.ArgumentParser(
        description=(
            "Regime check for behaviors observed in environments. Distinguishes "
            "regime mismatch from pathology by matching the behavior against a "
            "library of documented biological baselines and asking whether the "
            "current environment is one in which the behavior is adaptive."
        ),
    )
    parser.add_argument(
        "--behavior", "-b",
        help="Behavior or trait description to evaluate.",
    )
    parser.add_argument(
        "--environment", "-e",
        help="Description of the environment in which the behavior is observed.",
    )
    parser.add_argument(
        "--list-regimes", action="store_true",
        help="List all regime profiles in the library and exit.",
    )
    parser.add_argument(
        "--regime",
        help="Print the full profile for a single regime id and exit.",
    )
    parser.add_argument("--json", action="store_true", help="Output as JSON.")
    args = parser.parse_args()

    if args.list_regimes:
        if args.json:
            print(json.dumps([r.to_dict() for r in REGIMES.values()], indent=2))
        else:
            _print_regime_list()
        return

    if args.regime:
        regime = REGIMES.get(args.regime)
        if regime is None:
            print(f"unknown regime id: {args.regime}", file=sys.stderr)
            sys.exit(2)
        print(json.dumps(regime.to_dict(), indent=2))
        return

    if not args.behavior or not args.environment:
        parser.error("--behavior and --environment are both required (or use --list-regimes)")

    report = check_behavior(args.behavior, args.environment)
    if args.json:
        print(json.dumps(report.to_dict(), indent=2))
    else:
        _print_report(report)


if __name__ == "__main__":
    main()
