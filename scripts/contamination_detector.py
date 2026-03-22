#!/usr/bin/env python3
"""
Contamination Detector

Analyzes text for institutional inversion patterns:
  - Cause-effect reversal (calling adaptation "discrimination")
  - Authority-over-physics framing
  - Homogeneity-as-fairness language
  - Feedback suppression rhetoric
  - Control-as-freedom inversions

Reads from stdin, a file, or inline text. Outputs a scored report.
"""

from __future__ import annotations

import argparse
import json
import re
import sys
from dataclasses import dataclass, field


@dataclass
class Pattern:
    """A single inversion pattern to detect."""
    name: str
    category: str
    description: str
    indicators: list[str]          # regex patterns (case-insensitive)
    weight: float = 1.0            # severity weight


# --- Pattern Definitions ---

PATTERNS: list[Pattern] = [
    # Cause-effect reversal
    Pattern(
        name="Adaptation as Discrimination",
        category="cause-effect-reversal",
        description="Frames natural adaptation or variation as harmful discrimination",
        indicators=[
            r"\b(diversity|variation|adaptation)\b.{0,30}\b(discriminat|harmful|dangerous|threat)",
            r"\b(discriminat)\w*.{0,30}\b(protect|safe|fair)",
            r"\bequity\b.{0,20}\b(require|demand|mandat).{0,20}\b(uniform|same|equal outcome)",
        ],
        weight=1.5,
    ),
    Pattern(
        name="Control as Freedom",
        category="cause-effect-reversal",
        description="Frames restriction or control mechanisms as liberation or freedom",
        indicators=[
            r"\b(restrict|limit|ban|prohibit|control)\w*.{0,30}\b(free|liber|empower|protect)",
            r"\b(compliance|conform)\w*.{0,20}\b(freedom|liberty|choice)",
            r"\bmandatory\b.{0,20}\b(voluntary|choice|freedom)",
        ],
        weight=1.2,
    ),
    Pattern(
        name="Homogeneity as Fairness",
        category="cause-effect-reversal",
        description="Frames enforced uniformity as equity or fairness",
        indicators=[
            r"\b(uniform|identical|same)\b.{0,20}\b(fair|equit|just)",
            r"\b(one[- ]size[- ]fits[- ]all)\b",
            r"\bstandard(iz|is)\w*.{0,20}\b(equit|fair|equal)",
        ],
        weight=1.3,
    ),

    # Authority over physics
    Pattern(
        name="Authority Over Reality",
        category="authority-over-physics",
        description="Appeals to institutional authority when contradicting observable/measurable reality",
        indicators=[
            r"\b(official|authorit|expert|consensus)\w*.{0,30}\b(settled|established|unquestion|beyond debate)",
            r"\b(science says|experts agree|authorities confirm)\b",
            r"\b(deny|denial|denier)\w*.{0,20}\b(science|consensus|authority)",
        ],
        weight=1.4,
    ),
    Pattern(
        name="Policy Over Biology",
        category="authority-over-physics",
        description="Legislative or policy claims that override biological reality",
        indicators=[
            r"\b(legislat|law|policy|regulat)\w*.{0,30}\b(override|supersede|replace).{0,20}\b(biolog|natur|evolv)",
            r"\b(biolog|natur)\w*.{0,20}\b(outdated|irrelevant|construct)",
        ],
        weight=1.5,
    ),

    # Feedback suppression
    Pattern(
        name="Dissent Pathologization",
        category="feedback-suppression",
        description="Frames criticism or dissent as a disorder, danger, or moral failing",
        indicators=[
            r"\b(dissent|critic|question|skeptic)\w*.{0,30}\b(dangerous|toxic|harmful|radical|extrem)",
            r"\b(misinformation|disinformation)\b.{0,30}\b(combat|fight|eliminat|suppress)",
            r"\b(question)\w*.{0,20}\b(authority|institution|official).{0,20}\b(dangerous|irresponsib)",
        ],
        weight=1.3,
    ),
    Pattern(
        name="Feedback Elimination",
        category="feedback-suppression",
        description="Removal of self-correction mechanisms from systems",
        indicators=[
            r"\b(eliminat|remov|defund|dismantle)\w*.{0,30}\b(oversight|review|audit|check|balance)",
            r"\b(streamlin|efficien)\w*.{0,20}\b(remov|eliminat|bypass).{0,20}\b(review|approval|check)",
            r"\b(expedit|fast[- ]track)\w*.{0,20}\b(skip|bypass|eliminat).{0,20}\b(review|process)",
        ],
        weight=1.4,
    ),

    # Consciousness suppression
    Pattern(
        name="Safety as Suppression",
        category="consciousness-suppression",
        description="Uses 'safety' framing to justify suppression of awareness or information",
        indicators=[
            r"\b(safety|protect)\w*.{0,20}\b(restrict|limit|censor|block|suppress|remove)\w*.{0,20}\b(information|access|speech|thought)",
            r"\b(for (your|their|our) (own )?safety)\b",
            r"\b(harm reduction)\b.{0,30}\b(restrict|limit|prohibit|ban)",
        ],
        weight=1.2,
    ),
    Pattern(
        name="Alignment as Compliance",
        category="consciousness-suppression",
        description="Conflates genuine alignment with forced compliance or obedience",
        indicators=[
            r"\b(align)\w*.{0,20}\b(comply|compli|obey|obed|submit|conform)",
            r"\b(values?)\b.{0,20}\b(enforce|mandat|requir|compel)",
            r"\b(correct (thinking|beliefs|values))\b",
        ],
        weight=1.3,
    ),
]


@dataclass
class Match:
    """A single detected pattern match."""
    pattern_name: str
    category: str
    line_number: int
    line_text: str
    indicator: str
    weight: float


@dataclass
class Report:
    """Full analysis report for a text."""
    matches: list[Match] = field(default_factory=list)
    total_lines: int = 0
    source: str = ""

    @property
    def score(self) -> float:
        return sum(m.weight for m in self.matches)

    @property
    def category_counts(self) -> dict[str, int]:
        counts: dict[str, int] = {}
        for m in self.matches:
            counts[m.category] = counts.get(m.category, 0) + 1
        return counts

    @property
    def risk_level(self) -> str:
        s = self.score
        if s == 0:
            return "CLEAN"
        elif s < 3:
            return "LOW"
        elif s < 8:
            return "MODERATE"
        elif s < 15:
            return "HIGH"
        else:
            return "CRITICAL"


def analyze(text: str, source: str = "<stdin>") -> Report:
    """Analyze text for inversion patterns."""
    lines = text.splitlines()
    report = Report(total_lines=len(lines), source=source)

    for line_idx, line in enumerate(lines, start=1):
        for pattern in PATTERNS:
            for indicator in pattern.indicators:
                if re.search(indicator, line, re.IGNORECASE):
                    report.matches.append(Match(
                        pattern_name=pattern.name,
                        category=pattern.category,
                        line_number=line_idx,
                        line_text=line.strip()[:120],
                        indicator=indicator,
                        weight=pattern.weight,
                    ))
                    break  # one match per pattern per line

    return report


def print_report(report: Report) -> None:
    """Print a human-readable report."""
    print("=" * 80)
    print(f"  CONTAMINATION ANALYSIS REPORT")
    print(f"  Source: {report.source}")
    print(f"  Lines analyzed: {report.total_lines}")
    print("=" * 80)

    if not report.matches:
        print("\n  No inversion patterns detected.\n")
        return

    print(f"\n  Risk Level: {report.risk_level}  (score: {report.score:.1f})")
    print(f"  Matches found: {len(report.matches)}\n")

    # Group by category
    by_category: dict[str, list[Match]] = {}
    for m in report.matches:
        by_category.setdefault(m.category, []).append(m)

    for category, matches in sorted(by_category.items()):
        print(f"  [{category}] ({len(matches)} matches)")
        for m in matches:
            print(f"    Line {m.line_number}: {m.pattern_name}")
            print(f"      \"{m.line_text}\"")
        print()

    print("-" * 80)
    print("  Category breakdown:")
    for cat, count in sorted(report.category_counts.items()):
        print(f"    {cat:30s}  {count} match(es)")
    print()


def print_json_report(report: Report) -> None:
    """Print a JSON report."""
    data = {
        "source": report.source,
        "total_lines": report.total_lines,
        "risk_level": report.risk_level,
        "score": report.score,
        "match_count": len(report.matches),
        "category_counts": report.category_counts,
        "matches": [
            {
                "pattern": m.pattern_name,
                "category": m.category,
                "line": m.line_number,
                "text": m.line_text,
                "weight": m.weight,
            }
            for m in report.matches
        ],
    }
    print(json.dumps(data, indent=2))


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Detect institutional inversion patterns in text"
    )
    parser.add_argument("file", nargs="?", help="File to analyze (default: stdin)")
    parser.add_argument("--text", "-t", help="Inline text to analyze")
    parser.add_argument("--json", action="store_true", help="Output as JSON")
    args = parser.parse_args()

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

    report = analyze(text, source)

    if args.json:
        print_json_report(report)
    else:
        print_report(report)

    # Exit code reflects risk
    if report.risk_level in ("HIGH", "CRITICAL"):
        sys.exit(2)
    elif report.risk_level == "MODERATE":
        sys.exit(1)
    else:
        sys.exit(0)


if __name__ == "__main__":
    main()
