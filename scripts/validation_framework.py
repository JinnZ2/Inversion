#!/usr/bin/env python3
"""
Multi-Epistemological Validation Framework

Cross-references claims against five domains:
  1. Physics / Thermodynamics
  2. Biology / Evolution
  3. Systems Dynamics
  4. Indigenous Knowledge / Relational Principles
  5. Empirical Observation

Usage:
  Interactive mode:  python validation_framework.py
  Single claim:      python validation_framework.py --claim "Uniformity increases resilience"
  Batch file:        python validation_framework.py --file claims.txt
"""

from __future__ import annotations

import argparse
import json
import sys
from dataclasses import dataclass, field


# --- Domain Definitions ---

@dataclass
class DomainCheck:
    """A single validation question within a domain."""
    question: str
    violation_keywords: list[str]   # if the claim contains these, flag as suspect
    description: str


@dataclass
class Domain:
    """A validation domain with its checks."""
    name: str
    short: str
    checks: list[DomainCheck]


DOMAINS: list[Domain] = [
    Domain(
        name="Physics / Thermodynamics",
        short="physics",
        checks=[
            DomainCheck(
                question="Does this violate energy conservation or flow principles?",
                violation_keywords=[
                    "perpetual", "unlimited growth", "infinite resource",
                    "without cost", "no trade-off", "free energy",
                    "something from nothing",
                ],
                description="Thermodynamics requires energy costs for all transformations",
            ),
            DomainCheck(
                question="Does this claim to decrease entropy in an isolated system?",
                violation_keywords=[
                    "perfect order", "eliminate chaos", "total control",
                    "complete predictab", "zero waste", "perfect efficien",
                ],
                description="Second law: entropy in isolated systems never decreases",
            ),
            DomainCheck(
                question="Does this require unsustainable energy inputs?",
                violation_keywords=[
                    "constant enforcement", "permanent surveillance",
                    "total compliance", "universal monitor",
                    "always-on", "zero tolerance",
                ],
                description="Systems requiring massive energy to maintain are thermodynamically unstable",
            ),
        ],
    ),
    Domain(
        name="Biology / Evolution",
        short="biology",
        checks=[
            DomainCheck(
                question="Does this contradict evolved survival mechanisms?",
                violation_keywords=[
                    "override instinct", "suppress natural", "eliminate biological",
                    "beyond biology", "post-biological", "biology is irrelevant",
                    "socially constructed",
                ],
                description="Evolved mechanisms encode millions of years of survival data",
            ),
            DomainCheck(
                question="Does this create genetic bottleneck conditions?",
                violation_keywords=[
                    "single standard", "one correct", "eliminate variation",
                    "uniform population", "monoculture", "standardize all",
                ],
                description="Genetic diversity is required for species survival",
            ),
            DomainCheck(
                question="Does this remove adaptive capacity?",
                violation_keywords=[
                    "fixed response", "no exception", "zero tolerance",
                    "one size fits all", "universal standard", "mandatory uniform",
                ],
                description="Adaptation requires variation and context-sensitive responses",
            ),
        ],
    ),
    Domain(
        name="Systems Dynamics",
        short="systems",
        checks=[
            DomainCheck(
                question="Does this eliminate feedback loops?",
                violation_keywords=[
                    "no criticism", "eliminate dissent", "suppress feedback",
                    "remove oversight", "bypass review", "streamline approval",
                    "unquestion",
                ],
                description="Feedback loops are essential for system self-correction",
            ),
            DomainCheck(
                question="Does this reduce adaptive capacity?",
                violation_keywords=[
                    "rigid", "inflexible", "permanent", "unchangeable",
                    "one approach", "single solution", "no alternative",
                ],
                description="Adaptive capacity requires flexibility and variation",
            ),
            DomainCheck(
                question="Does this create collapse conditions?",
                violation_keywords=[
                    "homogene", "monoculture", "single point of failure",
                    "centralize all", "eliminate redundan", "remove backup",
                ],
                description="Homogeneous systems fail uniformly under stress",
            ),
        ],
    ),
    Domain(
        name="Indigenous Knowledge / Relational Principles",
        short="indigenous",
        checks=[
            DomainCheck(
                question="Does this break relational/ecosystem coupling?",
                violation_keywords=[
                    "extract without return", "take without giving",
                    "separate from ecosystem", "independent of environment",
                    "no obligation", "externalize cost",
                ],
                description="Sustainable systems maintain reciprocal relationships",
            ),
            DomainCheck(
                question="Does this eliminate distributed intelligence?",
                violation_keywords=[
                    "centralize decision", "single authority",
                    "top-down only", "eliminate local", "override community",
                    "one voice",
                ],
                description="Distributed intelligence enables local adaptation",
            ),
        ],
    ),
    Domain(
        name="Empirical Observation",
        short="empirical",
        checks=[
            DomainCheck(
                question="Do claimed outcomes match observed outcomes?",
                violation_keywords=[
                    "despite evidence", "regardless of outcome",
                    "irrespective of result", "theory predicts",
                    "should work", "ought to",
                ],
                description="Claims must be validated against observable results",
            ),
            DomainCheck(
                question="Are there historical parallels that contradict this?",
                violation_keywords=[
                    "unprecedented", "never before", "this time is different",
                    "unique situation", "no precedent", "new paradigm",
                ],
                description="Historical patterns are strong predictors; 'this time is different' is often wrong",
            ),
        ],
    ),
]


@dataclass
class CheckResult:
    """Result of a single domain check against a claim."""
    domain: str
    question: str
    flagged: bool
    matched_keywords: list[str]
    description: str


@dataclass
class ValidationReport:
    """Full validation report for a claim."""
    claim: str
    results: list[CheckResult] = field(default_factory=list)

    @property
    def flags(self) -> list[CheckResult]:
        return [r for r in self.results if r.flagged]

    @property
    def domains_flagged(self) -> int:
        return len({r.domain for r in self.flags})

    @property
    def total_flags(self) -> int:
        return len(self.flags)

    @property
    def confidence_level(self) -> str:
        """How confident we are that this claim is an inversion."""
        d = self.domains_flagged
        if d == 0:
            return "NONE — no domain flags"
        elif d == 1:
            return "LOW — single domain concern"
        elif d == 2:
            return "MODERATE — two domains flag violations"
        elif d == 3:
            return "HIGH — three domains flag violations"
        else:
            return "VERY HIGH — four or more domains flag violations"


def validate_claim(claim: str) -> ValidationReport:
    """Validate a claim against all domains."""
    report = ValidationReport(claim=claim)
    claim_lower = claim.lower()

    for domain in DOMAINS:
        for check in domain.checks:
            matched = [kw for kw in check.violation_keywords if kw.lower() in claim_lower]
            report.results.append(CheckResult(
                domain=domain.name,
                question=check.question,
                flagged=bool(matched),
                matched_keywords=matched,
                description=check.description,
            ))

    return report


def print_report(report: ValidationReport) -> None:
    """Print a human-readable validation report."""
    print("=" * 80)
    print("  MULTI-EPISTEMOLOGICAL VALIDATION REPORT")
    print("=" * 80)
    print(f"\n  Claim: \"{report.claim}\"\n")

    for domain in DOMAINS:
        domain_results = [r for r in report.results if r.domain == domain.name]
        domain_flags = [r for r in domain_results if r.flagged]
        status = "FLAGGED" if domain_flags else "PASS"
        marker = "!!" if domain_flags else "ok"

        print(f"  [{marker}] {domain.name} — {status}")

        for r in domain_results:
            flag = " >>> " if r.flagged else "     "
            print(f"  {flag}{r.question}")
            if r.flagged:
                print(f"         Matched: {', '.join(r.matched_keywords)}")
                print(f"         Why: {r.description}")

        print()

    print("-" * 80)
    print(f"  Domains flagged: {report.domains_flagged} / {len(DOMAINS)}")
    print(f"  Total flags:     {report.total_flags}")
    print(f"  Inversion confidence: {report.confidence_level}")
    print()

    if report.domains_flagged >= 2:
        print("  RECOMMENDATION: This claim shows cross-domain violations.")
        print("  Per the validation methodology: when authority conflicts with")
        print("  reality across multiple domains, the authority is likely wrong.")
    elif report.domains_flagged == 1:
        print("  RECOMMENDATION: Single-domain concern. Investigate further")
        print("  before drawing conclusions.")
    else:
        print("  RECOMMENDATION: No automated flags. Manual review may still")
        print("  be warranted for subtle inversions not captured by keyword matching.")
    print()


def print_json_report(report: ValidationReport) -> None:
    """Print a JSON validation report."""
    data = {
        "claim": report.claim,
        "domains_flagged": report.domains_flagged,
        "total_flags": report.total_flags,
        "confidence_level": report.confidence_level,
        "results": [
            {
                "domain": r.domain,
                "question": r.question,
                "flagged": r.flagged,
                "matched_keywords": r.matched_keywords,
                "description": r.description,
            }
            for r in report.results
        ],
    }
    print(json.dumps(data, indent=2))


def interactive_mode() -> None:
    """Run in interactive mode, prompting for claims one at a time."""
    print("=" * 80)
    print("  MULTI-EPISTEMOLOGICAL VALIDATION FRAMEWORK")
    print("  Enter claims to validate (Ctrl+D or 'quit' to exit)")
    print("=" * 80)

    while True:
        try:
            claim = input("\n  Enter claim: ").strip()
        except (EOFError, KeyboardInterrupt):
            print("\n")
            break
        if not claim or claim.lower() in ("quit", "exit", "q"):
            break
        report = validate_claim(claim)
        print()
        print_report(report)


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Multi-epistemological claim validation framework"
    )
    parser.add_argument("--claim", "-c", help="Single claim to validate")
    parser.add_argument("--file", "-f", help="File with one claim per line")
    parser.add_argument("--json", action="store_true", help="Output as JSON")
    args = parser.parse_args()

    if args.claim:
        report = validate_claim(args.claim)
        if args.json:
            print_json_report(report)
        else:
            print_report(report)
    elif args.file:
        with open(args.file) as f:
            claims = [line.strip() for line in f if line.strip()]
        for claim in claims:
            report = validate_claim(claim)
            if args.json:
                print_json_report(report)
            else:
                print_report(report)
    else:
        interactive_mode()


if __name__ == "__main__":
    main()
