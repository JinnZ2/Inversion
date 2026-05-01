#!/usr/bin/env python3
"""
Validity-Weighted Reweighting -- score claims by validity, not by frequency.

Standard AI/LLM weighting:
    claim_weight = f(citation_count, repetition, recency)

This module:
    claim_weight = f(
        premise_validity,
        evidence_strength,
        population_fit,
        contradiction_load,
        backward_trace_depth,
    )

A single well-grounded study outweighs a thousand repetitions standing on
a fragile shared premise.

Components:

  premise_validity_score   mean evidence_strength of the claim's root
                           premises, penalized by their mean fragility
                           (high-confidence + low-evidence = high fragility)
  population_fit_score     overlap of the study's population scope and
                           methodology controls with the population the
                           question is about
  contradiction_penalty    if a contradicting claim has higher premise
                           validity, take the differential as penalty
  raw_citation_weight      sum of citations across asserting studies,
                           normalized to the corpus max -- the foil for
                           the validity weight

Final:
    validity_weight = premise_validity * population_fit * (1 - penalty)

The `divergence_report` surfaces claims where citation weight and validity
weight differ sharply: overcited_undergrounded (loud but fragile) and
undercited_grounded (quiet but solid). These are the danger zones for
frequency-weighted retrieval systems.

Depends on `premise_cross_domain_audit.PremiseAuditEngine`. Stdlib only.
"""

from __future__ import annotations

import argparse
import json
import sys
from collections import defaultdict
from dataclasses import asdict, dataclass, field
from typing import Any

from scripts.audit.premise_cross_domain_audit import (
    DomainClaim,
    Premise,
    PremiseAuditEngine,
    build_demo_engine,
)


# ---------------------------------------------------------------------------
# Data structures
# ---------------------------------------------------------------------------


@dataclass
class Study:
    """Citation-bearing wrapper around one or more DomainClaims, with
    population scope metadata."""

    study_id: str
    title: str
    claim_ids: list[str]
    citation_count: int = 0
    sample_size: int = 0
    population_scope: set[str] = field(default_factory=set)
    methodology_controls: set[str] = field(default_factory=set)
    declared_limitations: list[str] = field(default_factory=list)


@dataclass
class PopulationContext:
    """The population the question is actually being asked about."""

    context_id: str
    descriptors: set[str] = field(default_factory=set)
    required_controls: set[str] = field(default_factory=set)


@dataclass
class WeightedClaim:
    claim_id: str
    statement: str
    domain: str
    raw_citation_weight: float
    validity_weight: float
    population_fit: float
    premise_validity: float
    contradiction_penalty: float
    explanation: list[str] = field(default_factory=list)

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


# ---------------------------------------------------------------------------
# Reweighting engine
# ---------------------------------------------------------------------------


class ValidityReweighter:
    def __init__(self, audit_engine: PremiseAuditEngine) -> None:
        self.engine = audit_engine
        self.studies: dict[str, Study] = {}
        self.claim_to_studies: dict[str, list[str]] = defaultdict(list)

    def add_study(self, study: Study) -> None:
        self.studies[study.study_id] = study
        for claim_id in study.claim_ids:
            self.claim_to_studies[claim_id].append(study.study_id)

    # -- component scores ------------------------------------------------

    def premise_validity_score(self, claim_id: str) -> tuple[float, list[str]]:
        """Mean evidence_strength of root premises minus mean fragility."""
        notes: list[str] = []
        roots = self.engine.find_root_premises(claim_id)
        if not roots:
            return 0.5, ["no traceable premises -- assumed neutral"]

        evidence_scores: list[float] = []
        fragility_scores: list[float] = []
        for premise_id in roots:
            premise = self.engine.premises.get(premise_id)
            if not premise:
                continue
            evidence_scores.append(premise.evidence_strength)
            fragility_scores.append(premise.fragility())

        if not evidence_scores:
            return 0.5, ["premises referenced but not defined"]

        mean_evidence = sum(evidence_scores) / len(evidence_scores)
        mean_fragility = sum(fragility_scores) / len(fragility_scores)
        validity = max(0.0, mean_evidence - mean_fragility)
        notes.append(
            f"mean_evidence={round(mean_evidence, 3)}, "
            f"mean_fragility={round(mean_fragility, 3)}"
        )
        return round(validity, 3), notes

    def population_fit_score(
        self, study_id: str, context: PopulationContext,
    ) -> tuple[float, list[str]]:
        """Overlap of study's population scope and methodology controls
        with the question's population."""
        notes: list[str] = []
        study = self.studies.get(study_id)
        if not study:
            return 0.0, ["study not found"]

        if context.descriptors:
            descriptor_overlap = len(
                study.population_scope & context.descriptors
            ) / max(len(context.descriptors), 1)
        else:
            descriptor_overlap = 0.5

        if context.required_controls:
            controls_present = len(
                study.methodology_controls & context.required_controls
            ) / len(context.required_controls)
        else:
            controls_present = 1.0

        fit = (descriptor_overlap + controls_present) / 2.0
        notes.append(
            f"descriptor_overlap={round(descriptor_overlap, 3)}, "
            f"controls_present={round(controls_present, 3)}"
        )
        missing_controls = context.required_controls - study.methodology_controls
        if missing_controls:
            notes.append(
                f"missing required controls: {sorted(missing_controls)}"
            )
        return round(fit, 3), notes

    def contradiction_penalty(self, claim_id: str) -> tuple[float, list[str]]:
        """If a contradicting claim has higher validity, take the differential."""
        notes: list[str] = []
        claim = self.engine.claims.get(claim_id)
        if not claim:
            return 0.0, []

        penalty = 0.0
        for other_id in claim.contradicts:
            if other_id not in self.engine.claims:
                continue
            self_validity, _ = self.premise_validity_score(claim_id)
            other_validity, _ = self.premise_validity_score(other_id)
            if other_validity > self_validity:
                differential = other_validity - self_validity
                penalty += differential
                notes.append(
                    f"contradicted by {other_id} "
                    f"(higher validity by {round(differential, 3)})"
                )
        return round(min(penalty, 1.0), 3), notes

    def raw_citation_weight(self, claim_id: str) -> float:
        """Sum of citation counts across asserting studies, normalized to
        the corpus maximum."""
        if not self.studies:
            return 0.0
        max_citations = max(
            (s.citation_count for s in self.studies.values()),
            default=1,
        )
        if max_citations == 0:
            return 0.0
        total = sum(
            self.studies[sid].citation_count
            for sid in self.claim_to_studies.get(claim_id, [])
            if sid in self.studies
        )
        return round(total / max_citations, 3)

    # -- final weighting -------------------------------------------------

    def weigh_claim(
        self,
        claim_id: str,
        context: PopulationContext | None = None,
    ) -> WeightedClaim:
        """Compute validity-weighted score for a claim.

        validity_weight = premise_validity
                          * mean(population_fit across asserting studies)
                          * (1 - contradiction_penalty)
        """
        claim = self.engine.claims.get(claim_id)
        if not claim:
            raise KeyError(f"Unknown claim: {claim_id}")

        explanation: list[str] = []

        premise_validity, notes = self.premise_validity_score(claim_id)
        explanation.append(f"premise_validity={premise_validity}")
        explanation.extend(notes)

        if context:
            fits: list[float] = []
            for sid in self.claim_to_studies.get(claim_id, []):
                fit, fit_notes = self.population_fit_score(sid, context)
                fits.append(fit)
                explanation.append(f"study {sid}: fit={fit}")
                explanation.extend(fit_notes)
            population_fit = sum(fits) / len(fits) if fits else 0.5
        else:
            population_fit = 1.0

        penalty, pen_notes = self.contradiction_penalty(claim_id)
        explanation.append(f"contradiction_penalty={penalty}")
        explanation.extend(pen_notes)

        validity_weight = round(
            premise_validity * population_fit * (1.0 - penalty), 3,
        )
        raw_citations = self.raw_citation_weight(claim_id)

        return WeightedClaim(
            claim_id=claim_id,
            statement=claim.statement,
            domain=claim.domain,
            raw_citation_weight=raw_citations,
            validity_weight=validity_weight,
            population_fit=round(population_fit, 3),
            premise_validity=premise_validity,
            contradiction_penalty=penalty,
            explanation=explanation,
        )

    def rank_corpus(
        self, context: PopulationContext | None = None,
    ) -> list[WeightedClaim]:
        """Rank every claim in the audit engine by validity-weighted score."""
        results = [self.weigh_claim(cid, context) for cid in self.engine.claims]
        results.sort(key=lambda w: w.validity_weight, reverse=True)
        return results

    def divergence_report(
        self,
        context: PopulationContext | None = None,
        threshold: float = 0.2,
    ) -> list[dict[str, Any]]:
        """Find claims where citation weight and validity weight diverge.

        Positive divergence = overcited_undergrounded (loud but fragile).
        Negative divergence = undercited_grounded (quiet but solid).
        """
        report: list[dict[str, Any]] = []
        for w in self.rank_corpus(context):
            divergence = round(w.raw_citation_weight - w.validity_weight, 3)
            if abs(divergence) >= threshold:
                report.append({
                    "claim_id": w.claim_id,
                    "statement": w.statement,
                    "domain": w.domain,
                    "raw_citation_weight": w.raw_citation_weight,
                    "validity_weight": w.validity_weight,
                    "divergence": divergence,
                    "type": (
                        "overcited_undergrounded" if divergence > 0
                        else "undercited_grounded"
                    ),
                })
        report.sort(key=lambda r: abs(r["divergence"]), reverse=True)
        return report


# ---------------------------------------------------------------------------
# Demo: dominance vs cooperation, with citation-weighted vs validity-weighted
# ---------------------------------------------------------------------------


def build_demo_reweighter() -> ValidityReweighter:
    """Build a ValidityReweighter on top of the premise audit demo engine,
    with four reference studies illustrating the citation/validity gap.

    Two heavily-cited studies (S1, S2) assert C2 (aggressive signaling
    increases attractiveness) on the fragile P1 premise. One quieter study
    (S3) supports C4 (chronic stress reduces fertility) on the well-grounded
    P2 premise with stronger methodology controls. S4 supports C5 (caregiver
    presence) on P2.
    """
    rw = ValidityReweighter(build_demo_engine())

    rw.add_study(Study(
        study_id="S1",
        title="Display dominance and mate choice in Western undergrads",
        claim_ids=["C2"],
        citation_count=500,
        sample_size=200,
        population_scope={"industrialized", "western", "urban", "untrained"},
        methodology_controls=set(),
        declared_limitations=["WEIRD sample only"],
    ))
    rw.add_study(Study(
        study_id="S2",
        title="Aggressive signaling reproductive outcomes meta-analysis",
        claim_ids=["C2"],
        citation_count=800,
        sample_size=15000,
        population_scope={"industrialized", "western"},
        methodology_controls={"meta_analysis"},
        declared_limitations=["heterogeneous methods"],
    ))
    rw.add_study(Study(
        study_id="S3",
        title="Cortisol load and reproductive endocrinology",
        claim_ids=["C4"],
        citation_count=120,
        sample_size=800,
        population_scope={
            "industrialized", "rural", "subsistence",
            "matched_age", "matched_lean_mass",
        },
        methodology_controls={
            "matched_lean_mass", "matched_training_history", "longitudinal",
        },
        declared_limitations=["modest sample"],
    ))
    rw.add_study(Study(
        study_id="S4",
        title="Caregiver presence and child outcomes longitudinal",
        claim_ids=["C5"],
        citation_count=60,
        sample_size=2000,
        population_scope={"rural", "subsistence", "multigenerational"},
        methodology_controls={"longitudinal", "matched_socioeconomic"},
        declared_limitations=[],
    ))
    return rw


def _demo_context() -> PopulationContext:
    return PopulationContext(
        context_id="rural_multigenerational_labor",
        descriptors={
            "rural", "subsistence", "multigenerational", "matched_lean_mass",
        },
        required_controls={"matched_lean_mass", "matched_training_history"},
    )


def _print_demo(rw: ValidityReweighter, context: PopulationContext) -> None:
    print("=" * 70)
    print(f"VALIDITY-WEIGHTED RANKING (context = {context.context_id})")
    print("=" * 70)
    for w in rw.rank_corpus(context):
        print(
            f"  {w.claim_id} [{w.domain}] "
            f"validity={w.validity_weight} "
            f"citation_freq={w.raw_citation_weight} "
            f"premise_validity={w.premise_validity} "
            f"pop_fit={w.population_fit} "
            f"contradiction_penalty={w.contradiction_penalty}"
        )
        print(f"     {w.statement}")

    print("\n" + "=" * 70)
    print("DIVERGENCE REPORT (citations vs validity)")
    print("=" * 70)
    for entry in rw.divergence_report(context):
        print(json.dumps(entry, indent=2))


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------


def main() -> int:
    parser = argparse.ArgumentParser(
        description=(
            "Reweight claims by premise validity rather than citation "
            "frequency. Surfaces claims that are loud but fragile "
            "(overcited_undergrounded) and quiet but solid "
            "(undercited_grounded)."
        ),
    )
    parser.add_argument(
        "--demo", action="store_true",
        help="run the built-in dominance-vs-cooperation demo (default).",
    )
    parser.add_argument(
        "--rank", action="store_true",
        help="emit the validity-weighted ranking only.",
    )
    parser.add_argument(
        "--divergence", action="store_true",
        help="emit the citation-vs-validity divergence report only.",
    )
    parser.add_argument(
        "--threshold", type=float, default=0.2,
        help="absolute divergence threshold for --divergence (default 0.2)",
    )
    parser.add_argument(
        "--no-context", action="store_true",
        help="skip population-context filtering (population_fit treated as 1.0)",
    )
    parser.add_argument("--json", action="store_true", help="machine-readable output.")
    args = parser.parse_args()

    rw = build_demo_reweighter()
    context = None if args.no_context else _demo_context()

    if args.rank:
        ranked = rw.rank_corpus(context)
        if args.json:
            print(json.dumps([w.to_dict() for w in ranked], indent=2))
        else:
            for w in ranked:
                print(
                    f"{w.claim_id} [{w.domain}] "
                    f"validity={w.validity_weight} "
                    f"citation_freq={w.raw_citation_weight}"
                )
        return 0

    if args.divergence:
        report = rw.divergence_report(context, threshold=args.threshold)
        if args.json:
            print(json.dumps(report, indent=2))
        else:
            for entry in report:
                print(json.dumps(entry, indent=2))
        return 0

    if args.demo or len(sys.argv) == 1:
        if args.json:
            print(json.dumps({
                "ranking": [w.to_dict() for w in rw.rank_corpus(context)],
                "divergence": rw.divergence_report(context, threshold=args.threshold),
            }, indent=2))
        else:
            _print_demo(rw, context or _demo_context())
        return 0

    parser.print_help()
    return 1


if __name__ == "__main__":
    sys.exit(main())
