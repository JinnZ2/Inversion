#!/usr/bin/env python3
"""
Premise Cross-Domain Audit -- premise tracing and repercussion analysis.

Detects:

  1. Shared hidden premises across domains (a single premise propagating
     into economics, dating culture, organizational behavior, etc.)
  2. Contradictions between claims, with root-premise trace
  3. Premise propagation chains (forward: failed premise -> dependent
     claims -> claims those claims support; backward: suspect claim ->
     all premises it inherited)
  4. Repercussion cascades when a premise is invalidated, with confidence-
     weighted severity (high belief + low evidence = highest cascade)
  5. Confidence-weighted fragility (high belief + weak evidence = danger
     zone; these are the premises that propagate widest before being checked)
  6. Circular dependency chains in the claim graph

The fragility score is the load-bearing signal: a premise with high
confidence and low evidence is the most dangerous kind, because it
propagates into many domains before its grounding is questioned.

CC0. Stdlib only.
"""

from __future__ import annotations

import argparse
import json
import sys
from collections import defaultdict, deque
from dataclasses import dataclass, field
from typing import Any


# ---------------------------------------------------------------------------
# Data structures
# ---------------------------------------------------------------------------


@dataclass
class Premise:
    premise_id: str
    statement: str
    confidence: float = 0.5         # how strongly believed
    evidence_strength: float = 0.5  # how well grounded in evidence
    source_domains: set[str] = field(default_factory=set)
    tags: set[str] = field(default_factory=set)

    def fragility(self) -> float:
        """High belief + weak evidence = maximum fragility.

        This is the danger-zone signal: premises accepted without
        grounding propagate widely before being checked.
        """
        return round(self.confidence * (1.0 - self.evidence_strength), 3)


@dataclass
class DomainClaim:
    domain: str
    claim_id: str
    statement: str
    depends_on: list[str] = field(default_factory=list)
    supports: list[str] = field(default_factory=list)
    contradicts: list[str] = field(default_factory=list)


@dataclass
class Repercussion:
    affected_domain: str
    affected_claim: str
    severity: float
    explanation: str

    def to_dict(self) -> dict[str, Any]:
        return {
            "affected_domain": self.affected_domain,
            "affected_claim": self.affected_claim,
            "severity": self.severity,
            "explanation": self.explanation,
        }


# ---------------------------------------------------------------------------
# Audit engine
# ---------------------------------------------------------------------------


class PremiseAuditEngine:
    def __init__(self) -> None:
        self.premises: dict[str, Premise] = {}
        self.claims: dict[str, DomainClaim] = {}
        self.domain_index: dict[str, list[str]] = defaultdict(list)
        self.premise_to_claims: dict[str, list[str]] = defaultdict(list)

    # -- registration ----------------------------------------------------

    def add_premise(self, premise: Premise) -> None:
        self.premises[premise.premise_id] = premise

    def add_claim(self, claim: DomainClaim) -> None:
        self.claims[claim.claim_id] = claim
        self.domain_index[claim.domain].append(claim.claim_id)
        for p in claim.depends_on:
            self.premise_to_claims[p].append(claim.claim_id)

    # -- cross-domain detection ------------------------------------------

    def detect_cross_domain_premises(self) -> dict[str, list[str]]:
        """Find premises used across multiple domains."""
        result: dict[str, list[str]] = {}
        for premise_id, claim_ids in self.premise_to_claims.items():
            domains = sorted({
                self.claims[c].domain
                for c in claim_ids
                if c in self.claims
            })
            if len(domains) >= 2:
                result[premise_id] = domains
        return result

    # -- contradictions --------------------------------------------------

    def detect_contradictions(self) -> list[tuple[str, str]]:
        """Return claim contradiction pairs (only those whose targets
        are registered claims)."""
        contradictions: list[tuple[str, str]] = []
        for claim_id, claim in self.claims.items():
            for other in claim.contradicts:
                if other in self.claims:
                    contradictions.append((claim_id, other))
        return contradictions

    # -- dependency graph ------------------------------------------------

    def premise_dependency_graph(self) -> dict[str, list[str]]:
        return {p: list(cs) for p, cs in self.premise_to_claims.items()}

    # -- forward propagation: premise -> dependent claims -> supports ----

    def propagate_premise_failure(
        self,
        failed_premise_id: str,
        decay: float = 0.85,
        use_confidence: bool = True,
    ) -> list[Repercussion]:
        """Simulate systemic impact when a premise becomes invalid.

        If ``use_confidence`` is True, initial severity is weighted by the
        premise's fragility score. A high-confidence/low-evidence premise
        produces the highest initial severity because it has propagated
        widest before validation.
        """
        if (
            use_confidence
            and failed_premise_id in self.premises
        ):
            premise = self.premises[failed_premise_id]
            initial_severity = max(premise.fragility(), 0.1)
        else:
            initial_severity = 1.0

        repercussions: list[Repercussion] = []
        visited: set[str] = set()
        queue: deque[tuple[str, float]] = deque()
        queue.append((failed_premise_id, initial_severity))

        while queue:
            current, severity = queue.popleft()
            if current in visited:
                continue
            visited.add(current)

            if current in self.premise_to_claims:
                for claim_id in self.premise_to_claims[current]:
                    claim = self.claims[claim_id]
                    repercussions.append(Repercussion(
                        affected_domain=claim.domain,
                        affected_claim=claim.statement,
                        severity=round(severity, 3),
                        explanation=(
                            f"Claim depends on failed premise "
                            f"'{failed_premise_id}'."
                        ),
                    ))
                    for next_claim in claim.supports:
                        queue.append((next_claim, severity * decay))
            elif current in self.claims:
                claim = self.claims[current]
                for next_claim in claim.supports:
                    queue.append((next_claim, severity * decay))

        return sorted(repercussions, key=lambda r: r.severity, reverse=True)

    # -- backward trace: claim -> root premises --------------------------

    def find_root_premises(self, suspect_claim_id: str) -> dict[str, list[str]]:
        """Trace backward from a suspect claim to find all premises it
        ultimately depends on, plus the trace path of intermediate claims.

        Use case: a claim contradicts lived data; this surfaces the hidden
        premises that produced it.
        """
        roots: dict[str, list[str]] = {}
        visited: set[str] = set()

        def trace(node_id: str, path: list[str]) -> None:
            if node_id in visited:
                return
            visited.add(node_id)
            if node_id in self.premises:
                roots[node_id] = list(path)
                return
            if node_id in self.claims:
                claim = self.claims[node_id]
                for dep in claim.depends_on:
                    trace(dep, path + [node_id])

        trace(suspect_claim_id, [])
        return roots

    def trace_contradiction_roots(self) -> list[dict[str, Any]]:
        """For every contradiction pair, surface the root premises on each
        side. Same premise on both sides => self-inflicted from a shared
        assumption. Different premises => framework conflict."""
        results: list[dict[str, Any]] = []
        for a, b in self.detect_contradictions():
            roots_a = self.find_root_premises(a)
            roots_b = self.find_root_premises(b)
            shared = sorted(set(roots_a.keys()) & set(roots_b.keys()))
            only_a = sorted(set(roots_a.keys()) - set(roots_b.keys()))
            only_b = sorted(set(roots_b.keys()) - set(roots_a.keys()))
            if shared and not (only_a or only_b):
                kind = "self_inflicted"
            elif only_a and only_b:
                kind = "framework_conflict"
            else:
                kind = "asymmetric"
            results.append({
                "claim_a": a,
                "claim_b": b,
                "shared_premises": shared,
                "premises_only_in_a": only_a,
                "premises_only_in_b": only_b,
                "type": kind,
            })
        return results

    # -- cycle detection -------------------------------------------------

    def detect_cycles(self) -> list[list[str]]:
        """Find circular dependency chains in the claim graph (A supports
        B supports ... back to A). Iterative DFS with path tracking."""
        cycles: list[list[str]] = []
        seen_cycles: set[tuple[str, ...]] = set()

        def normalize(cycle: list[str]) -> tuple[str, ...]:
            if not cycle:
                return tuple()
            min_idx = cycle.index(min(cycle))
            rotated = cycle[min_idx:] + cycle[:min_idx]
            return tuple(rotated)

        for start in self.claims:
            stack: list[tuple[str, list[str], set[str]]] = [
                (start, [start], {start})
            ]
            while stack:
                node, path, on_path = stack.pop()
                claim = self.claims.get(node)
                if not claim:
                    continue
                for nxt in claim.supports:
                    if nxt in on_path:
                        idx = path.index(nxt)
                        cycle = path[idx:]
                        key = normalize(cycle)
                        if key not in seen_cycles:
                            seen_cycles.add(key)
                            cycles.append(cycle)
                    elif nxt in self.claims:
                        new_on_path = on_path | {nxt}
                        stack.append((nxt, path + [nxt], new_on_path))
        return cycles

    # -- domain-level metrics --------------------------------------------

    def hidden_assumption_density(self) -> dict[str, float]:
        """Average dependencies-per-claim per domain."""
        scores: dict[str, float] = {}
        for domain, claim_ids in self.domain_index.items():
            if not claim_ids:
                scores[domain] = 0.0
                continue
            total_deps = sum(
                len(self.claims[c].depends_on) for c in claim_ids
            )
            scores[domain] = round(total_deps / len(claim_ids), 3)
        return scores

    # -- aggregate report ------------------------------------------------

    def epistemic_fragility_report(self) -> dict[str, Any]:
        cross_domain = self.detect_cross_domain_premises()
        fragility: list[dict[str, Any]] = []
        for premise_id, domains in cross_domain.items():
            premise = self.premises[premise_id]
            blast_radius = len(self.premise_to_claims[premise_id])
            base_risk = blast_radius * len(domains)
            weighted_risk = round(base_risk * (1 + premise.fragility()), 3)
            fragility.append({
                "premise_id": premise_id,
                "statement": premise.statement,
                "domains": domains,
                "blast_radius": blast_radius,
                "confidence": premise.confidence,
                "evidence_strength": premise.evidence_strength,
                "fragility_score": premise.fragility(),
                "risk_score": weighted_risk,
            })
        fragility.sort(key=lambda x: x["risk_score"], reverse=True)
        return {
            "cross_domain_premises": fragility,
            "contradictions": self.detect_contradictions(),
            "contradiction_roots": self.trace_contradiction_roots(),
            "domain_assumption_density": self.hidden_assumption_density(),
            "cycles": self.detect_cycles(),
        }

    # -- serialization ---------------------------------------------------

    def to_dict(self) -> dict[str, Any]:
        return {
            "premises": {
                k: {
                    "statement": v.statement,
                    "confidence": v.confidence,
                    "evidence_strength": v.evidence_strength,
                    "fragility": v.fragility(),
                    "source_domains": sorted(v.source_domains),
                    "tags": sorted(v.tags),
                }
                for k, v in self.premises.items()
            },
            "claims": {
                k: {
                    "domain": v.domain,
                    "statement": v.statement,
                    "depends_on": list(v.depends_on),
                    "supports": list(v.supports),
                    "contradicts": list(v.contradicts),
                }
                for k, v in self.claims.items()
            },
        }

    def export_json(self) -> str:
        return json.dumps(self.to_dict(), indent=2)

    # -- loaders ---------------------------------------------------------

    @classmethod
    def from_dict(cls, payload: dict[str, Any]) -> "PremiseAuditEngine":
        engine = cls()
        for pid, p in payload.get("premises", {}).items():
            engine.add_premise(Premise(
                premise_id=pid,
                statement=p.get("statement", ""),
                confidence=float(p.get("confidence", 0.5)),
                evidence_strength=float(p.get("evidence_strength", 0.5)),
                source_domains=set(p.get("source_domains", [])),
                tags=set(p.get("tags", [])),
            ))
        for cid, c in payload.get("claims", {}).items():
            engine.add_claim(DomainClaim(
                domain=c.get("domain", ""),
                claim_id=cid,
                statement=c.get("statement", ""),
                depends_on=list(c.get("depends_on", [])),
                supports=list(c.get("supports", [])),
                contradicts=list(c.get("contradicts", [])),
            ))
        return engine


# ---------------------------------------------------------------------------
# Demo engine: dominance vs cooperation across domains
# ---------------------------------------------------------------------------


def build_demo_engine() -> PremiseAuditEngine:
    engine = PremiseAuditEngine()

    engine.add_premise(Premise(
        premise_id="P1",
        statement="Male dominance behavior increases reproductive fitness.",
        confidence=0.8,
        evidence_strength=0.45,
        source_domains={"evolutionary_psychology", "economics", "dating_culture"},
        tags={"dominance", "status", "reproduction"},
    ))
    engine.add_premise(Premise(
        premise_id="P2",
        statement=(
            "Protective cooperative behavior improves long-term offspring "
            "survival."
        ),
        confidence=0.72,
        evidence_strength=0.8,
        source_domains={"anthropology", "developmental_psychology", "biology"},
        tags={"cooperation", "offspring", "protection"},
    ))

    engine.add_claim(DomainClaim(
        domain="economics",
        claim_id="C1",
        statement="Competitive dominance produces optimal leadership.",
        depends_on=["P1"],
        supports=["C3"],
    ))
    engine.add_claim(DomainClaim(
        domain="social_media",
        claim_id="C2",
        statement="Aggressive signaling increases male attractiveness.",
        depends_on=["P1"],
        contradicts=["C4"],
    ))
    engine.add_claim(DomainClaim(
        domain="organizational_behavior",
        claim_id="C3",
        statement="High-pressure dominance cultures improve productivity.",
        depends_on=["P1"],
    ))
    engine.add_claim(DomainClaim(
        domain="biology",
        claim_id="C4",
        statement="Chronic stress and aggression can reduce fertility.",
        depends_on=["P2"],
        contradicts=["C2"],
    ))
    engine.add_claim(DomainClaim(
        domain="developmental_psychology",
        claim_id="C5",
        statement="Stable caregiving environments improve child outcomes.",
        depends_on=["P2"],
    ))

    return engine


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------


def _print_demo(engine: PremiseAuditEngine) -> None:
    print("=" * 70)
    print("CROSS-DOMAIN PREMISES")
    print("=" * 70)
    for premise_id, domains in engine.detect_cross_domain_premises().items():
        print(f"  {premise_id}: {domains}")

    print("\n" + "=" * 70)
    print("CONTRADICTIONS")
    print("=" * 70)
    for a, b in engine.detect_contradictions():
        print(f"  {a} <-> {b}")

    print("\n" + "=" * 70)
    print("BACKWARD TRACE: roots of suspect claim C2")
    print("=" * 70)
    for premise_id, path in engine.find_root_premises("C2").items():
        print(f"  {premise_id} via path: {path}")

    print("\n" + "=" * 70)
    print("CONTRADICTION ROOT ANALYSIS")
    print("=" * 70)
    for entry in engine.trace_contradiction_roots():
        print(json.dumps(entry, indent=2))

    print("\n" + "=" * 70)
    print("FRAGILITY REPORT")
    print("=" * 70)
    print(json.dumps(engine.epistemic_fragility_report(), indent=2))

    print("\n" + "=" * 70)
    print("PREMISE FAILURE CASCADE (confidence-weighted): P1")
    print("=" * 70)
    for r in engine.propagate_premise_failure("P1"):
        print(f"  [{r.severity}] {r.affected_domain} -> {r.affected_claim}")

    print("\n" + "=" * 70)
    print("CYCLE DETECTION")
    print("=" * 70)
    cycles = engine.detect_cycles()
    if cycles:
        for c in cycles:
            print("  " + " -> ".join(c))
    else:
        print("  No cycles detected.")


def _load_engine(path: str | None) -> PremiseAuditEngine:
    if path:
        with open(path) as f:
            return PremiseAuditEngine.from_dict(json.load(f))
    return build_demo_engine()


def main() -> int:
    parser = argparse.ArgumentParser(
        description=(
            "Cross-domain premise tracing and repercussion analysis. "
            "Detects shared premises across domains, contradictions, "
            "forward/backward propagation, fragility (high-belief + "
            "low-evidence), and circular dependency chains."
        ),
    )
    parser.add_argument(
        "file", nargs="?",
        help=(
            "JSON file with {premises:{...}, claims:{...}} payload. "
            "If omitted, the built-in dominance-vs-cooperation demo is used."
        ),
    )
    parser.add_argument(
        "--demo", action="store_true",
        help="run the full demo report (default when no file is given).",
    )
    parser.add_argument(
        "--report", action="store_true",
        help="emit the epistemic fragility report only.",
    )
    parser.add_argument(
        "--propagate", metavar="PREMISE_ID",
        help="emit the failure-propagation cascade for a premise.",
    )
    parser.add_argument(
        "--no-confidence", action="store_true",
        help=(
            "with --propagate, ignore fragility weighting and start at "
            "severity 1.0."
        ),
    )
    parser.add_argument(
        "--roots", metavar="CLAIM_ID",
        help="emit the backward root-premise trace for a claim.",
    )
    parser.add_argument(
        "--export", action="store_true",
        help="emit the engine state as JSON ({premises, claims}).",
    )
    parser.add_argument("--json", action="store_true", help="machine-readable output.")
    args = parser.parse_args()

    engine = _load_engine(args.file)

    if args.export:
        print(engine.export_json())
        return 0

    if args.report:
        report = engine.epistemic_fragility_report()
        print(json.dumps(report, indent=2))
        return 0

    if args.propagate:
        cascade = engine.propagate_premise_failure(
            args.propagate, use_confidence=not args.no_confidence,
        )
        if args.json:
            print(json.dumps([r.to_dict() for r in cascade], indent=2))
        else:
            for r in cascade:
                print(f"[{r.severity}] {r.affected_domain} -> {r.affected_claim}")
                print(f"    {r.explanation}")
        return 0

    if args.roots:
        roots = engine.find_root_premises(args.roots)
        if args.json:
            print(json.dumps(roots, indent=2))
        else:
            if not roots:
                print(f"no premises found for claim {args.roots}")
            for premise_id, path in roots.items():
                print(f"{premise_id} via path: {path}")
        return 0

    if args.demo or args.file is None:
        if args.json:
            report = engine.epistemic_fragility_report()
            print(json.dumps(report, indent=2))
        else:
            _print_demo(engine)
        return 0

    parser.print_help()
    return 1


if __name__ == "__main__":
    sys.exit(main())
