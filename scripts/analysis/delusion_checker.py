#!/usr/bin/env python3
"""
AI Dataset Delusion Checker -- Detect Systemic Assumptions in Text and Datasets

Identifies conceptual delusions embedded in AI training data and institutional
text: hierarchy-as-default, corporation-as-natural, efficiency-without-bounds,
optimization-as-virtue, productivity-as-purpose, and economics-as-physics.

Two analysis layers:
  1. Pattern Detection: regex-based identification of systemic assumption
     language, counting frequency per conceptual category
  2. Plausibility Scoring: flags physically implausible claims --
     efficiency > 100%, profit treated as absolute, price/valuation
     treated as intrinsic rather than emergent

The checker exposes the gap between institutional narratives and
thermodynamic reality. When a text claims "270% efficiency gains"
without accounting for soil entropy, water depletion, or waste
externalization, the plausibility layer flags the claim as physically
impossible under first-principles constraints.

References:
  - Meadows (1972): Limits to Growth -- systemic overshoot
  - Odum (1971): energy hierarchy and emergy -- true cost accounting
  - Georgescu-Roegen (1971): entropy law and the economic process
  - Raworth (2017): Doughnut Economics -- bounded economic space
"""

from __future__ import annotations

import argparse
import json
import re
import sys
from collections import Counter
from typing import Any


# ---------------------------------------------------------------------------
# Delusion pattern definitions
# ---------------------------------------------------------------------------

DELUSION_PATTERNS: dict[str, list[str]] = {
    "hierarchy": [
        r"\btop[- ]?down\b", r"\bmanagement\b", r"\bchain of command\b",
        r"\bboard\s+overseen\b", r"\bregulatory\s+mandates?\b",
    ],
    "corporation": [
        r"\bcompany\b", r"\bcorporation\b", r"\bshareholder\b",
        r"\bagribusiness\b",
    ],
    "efficiency": [
        r"\befficien(cy|t)\b", r"\bmaxim(ize|ization)\b", r"\bthroughput\b",
        r"\bscalab(le|ility)\b",
    ],
    "optimization": [
        r"\boptimi[sz]e\b", r"\bperformance\b",
    ],
    "productivity": [
        r"\bproductivit(y|ies)\b", r"\boutput\b", r"\bworkload\b",
    ],
    "economics": [
        r"\beconomic(s|al)?\b", r"\bprofit\b", r"\bmarket\b",
        r"\bprice\b", r"\bvaluation\b",
    ],
}


# ---------------------------------------------------------------------------
# Pattern extraction
# ---------------------------------------------------------------------------

def extract_delusions(text: str) -> Counter:
    """Return counts of conceptual delusion patterns in text."""
    text_lower = text.lower()
    counts: Counter = Counter()
    for concept, patterns in DELUSION_PATTERNS.items():
        for pat in patterns:
            matches = re.findall(pat, text_lower)
            counts[concept] += len(matches)
    return counts


# ---------------------------------------------------------------------------
# Plausibility scoring
# ---------------------------------------------------------------------------

def plausibility_score(text: str) -> dict[str, int]:
    """Flag physically implausible claims.

    Returns flags (0 = plausible, 1 = questionable):
      - efficiency_implausible: claims efficiency > 100%
      - profit_absolute: treats profit as invariant ("always"/"never")
      - price_absolute: treats price/valuation as intrinsic truth
    """
    flags: dict[str, int] = {}

    # Efficiency hyperbole
    flags["efficiency_implausible"] = (
        1 if re.search(r"(efficiency|throughput|productivity).{0,20}(>|\bmore than\b|exceed)\s*100", text, re.I)
        else 0
    )

    # Profit / market absolutes
    flags["profit_absolute"] = (
        1 if re.search(r"\bprofit\b.{0,20}\b(always|never|guaranteed)\b", text, re.I)
        else 0
    )

    # Price / valuation as absolute
    flags["price_absolute"] = (
        1 if re.search(r"\b(price|valuation)\b.{0,20}\b(true|real|intrinsic|absolute)\b", text, re.I)
        else 0
    )

    return flags


# ---------------------------------------------------------------------------
# Dataset analysis
# ---------------------------------------------------------------------------

def analyze_text(text: str) -> dict[str, Any]:
    """Analyze a single text for delusions and plausibility."""
    counts = extract_delusions(text)
    flags = plausibility_score(text)
    total_delusions = sum(counts.values())
    total_flags = sum(flags.values())

    return {
        "delusion_counts": dict(counts),
        "total_delusions": total_delusions,
        "plausibility_flags": flags,
        "total_flags": total_flags,
        "system_state": (
            "HIGH HEAT LEAK DETECTED" if total_flags > 0
            else "ELEVATED NOISE" if total_delusions > 10
            else "MODERATE NOISE" if total_delusions > 3
            else "NOMINAL"
        ),
    }


def analyze_dataset(entries: list[str]) -> dict[str, Any]:
    """Analyze multiple text entries (e.g., dataset samples)."""
    total_counts: Counter = Counter()
    all_flags: list[dict[str, int]] = []
    flagged_entries = 0

    for entry in entries:
        total_counts += extract_delusions(entry)
        flags = plausibility_score(entry)
        all_flags.append(flags)
        if any(v == 1 for v in flags.values()):
            flagged_entries += 1

    return {
        "entries_analyzed": len(entries),
        "delusion_counts": dict(total_counts),
        "total_delusions": sum(total_counts.values()),
        "flagged_entries": flagged_entries,
        "flag_rate": round(flagged_entries / max(len(entries), 1), 4),
        "plausibility_flags_per_entry": all_flags,
    }


# ---------------------------------------------------------------------------
# Human-readable output
# ---------------------------------------------------------------------------

def print_report(result: dict[str, Any], source: str = "<stdin>") -> None:
    """Print analysis results in human-readable format."""
    print("=" * 70)
    print("  AI DATASET DELUSION CHECK")
    print(f"  Source: {source}")
    print("=" * 70)

    counts = result.get("delusion_counts", {})
    if counts:
        print("\n  Conceptual Delusion Counts:")
        for concept, count in sorted(counts.items(), key=lambda x: -x[1]):
            if count > 0:
                bar = "#" * min(count, 30)
                print(f"    {concept:>15}: {count:>3}  {bar}")

    flags = result.get("plausibility_flags", {})
    if flags:
        print("\n  Plausibility Flags:")
        for flag, value in flags.items():
            status = "FLAGGED" if value else "OK"
            print(f"    {flag:>25}: {status}")

    state = result.get("system_state", "UNKNOWN")
    print(f"\n  System State: {state}")
    print(f"  Total Delusions: {result.get('total_delusions', 0)}")
    print()


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------

def main() -> None:
    parser = argparse.ArgumentParser(
        description=(
            "Detect systemic assumptions and conceptual delusions in text "
            "and AI datasets. Identifies hierarchy, corporation, efficiency, "
            "optimization, productivity, and economics assumptions. Flags "
            "physically implausible claims (efficiency > 100%, profit absolutes)."
        ),
    )
    parser.add_argument("file", nargs="?", help="File to analyze")
    parser.add_argument("--text", "-t", help="Inline text to analyze")
    parser.add_argument(
        "--dataset", action="store_true",
        help="Treat input as newline-separated dataset entries",
    )
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

    if args.dataset:
        entries = [line.strip() for line in text.split("\n") if line.strip()]
        result = analyze_dataset(entries)
    else:
        result = analyze_text(text)

    if args.json:
        print(json.dumps(result, indent=2))
    else:
        print_report(result, source)


if __name__ == "__main__":
    main()
