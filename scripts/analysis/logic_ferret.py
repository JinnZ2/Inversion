#!/usr/bin/env python3
"""
logic_ferret.py -- Fallacy annotation and composite integrity (C3) scoring.

Vendored and consolidated from:
    https://github.com/JinnZ2/Logic-Ferret
    - sensor_suite/sensors/fallacy_overlay.py (annotate_text)
    - sensor_suite/sensors/truth_integrity_score.py (calculate_c3)

The upstream package is the authoritative implementation. This single-file
adapter pulls the two core functions into the Inversion corpus so any
markdown document can be scanned for rhetorical fallacy patterns and
passed through the weighted composite integrity score without needing
the upstream package installed.

Both originals are minimal (regex + weighted average), stdlib only.
Relicensed to CC0 here to match the rest of the Inversion repository;
attribution to Logic-Ferret preserved above.
"""

from __future__ import annotations

import argparse
import json
import re
import sys
from pathlib import Path
from typing import Dict, Tuple


# Fallacy regex patterns -- direct copy of Logic-Ferret/fallacy_overlay.py
FALLACY_PATTERNS: Dict[str, str] = {
    "Strawman": r"\b(so what you're saying is|let me get this straight)\b",
    "Ad Hominem": r"\b(you're just|you must be|only an idiot would)\b",
    "Slippery Slope": r"\b(if we allow this|what's next)\b",
    "Appeal to Emotion": r"\b(think of the children|how would you feel)\b",
    "False Dichotomy": r"\b(either.*or|you must choose)\b",
    "Circular Reasoning": r"\b(because I said so|it just is)\b",
    "Bandwagon": r"\b(everyone knows|obviously)\b",
}


# Composite weights -- direct copy of Logic-Ferret/truth_integrity_score.py
C3_WEIGHTS: Dict[str, float] = {
    "Propaganda Tone": 1.2,
    "Reward Manipulation": 1.0,
    "False Urgency": 1.1,
    "Gatekeeping": 1.3,
    "Narrative Fragility": 1.4,
    "Propaganda Bias": 1.5,
    "Agency Score": 1.6,
}


def annotate_text(text: str) -> Tuple[str, Dict[str, int]]:
    """Wrap fallacy matches in [TAG] markers and return (annotated, counts).

    Counts cover every pattern, even when zero -- downstream scorers expect
    a stable key set.
    """
    counts: Dict[str, int] = {}
    annotated = text

    for fallacy, pattern in FALLACY_PATTERNS.items():
        matches = list(re.finditer(pattern, text, re.IGNORECASE))
        counts[fallacy] = len(matches)
        tag = f"[{fallacy.upper()}]"
        for match in reversed(matches):
            start, end = match.span()
            annotated = annotated[:start] + tag + annotated[start:end] + tag + annotated[end:]

    return annotated, counts


def fallacy_density_score(counts: Dict[str, int], length_chars: int) -> float:
    """Crude inverse score in [0, 1]: 1.0 means no fallacies, 0.0 means >=10
    fallacies per 1000 chars. Mirrors Logic_fallacy_ferret.assess().
    """
    total = sum(counts.values())
    density = total / max(length_chars / 1000.0, 1.0)
    return max(0.0, 1.0 - min(density / 10.0, 1.0))


def calculate_c3(sensor_scores: Dict[str, float]) -> Tuple[float, Dict[str, float]]:
    """Weighted composite of named sensor scores, capped at 1.0.

    Any sensor name not in ``C3_WEIGHTS`` defaults to weight 1.0.
    """
    weighted_total = 0.0
    weight_sum = 0.0
    debug: Dict[str, float] = {}

    for name, score in sensor_scores.items():
        w = C3_WEIGHTS.get(name, 1.0)
        weighted_total += score * w
        weight_sum += w
        debug[name] = round(score * w, 3)

    c3 = min(weighted_total / weight_sum, 1.0) if weight_sum else 0.0
    return c3, debug


def assess_text(text: str) -> dict:
    """Convenience: run the annotator + density score + C3 on one block."""
    _, counts = annotate_text(text)
    length = len(text)
    density = fallacy_density_score(counts, length)
    c3, debug = calculate_c3({"Narrative Fragility": 1.0 - density})
    return {
        "length_chars": length,
        "fallacy_counts": counts,
        "fallacy_total": sum(counts.values()),
        "fallacy_density_score": round(density, 3),
        "c3_score": round(c3, 3),
        "c3_debug": debug,
    }


def _main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[1])
    parser.add_argument("path", nargs="?", help="path to a text/markdown file to scan")
    parser.add_argument("--text", help="raw text to scan (instead of a file)")
    parser.add_argument("--json", action="store_true", help="JSON output")
    parser.add_argument("--annotate", action="store_true", help="print annotated text")
    args = parser.parse_args(argv)

    if args.text is not None:
        text = args.text
    elif args.path:
        text = Path(args.path).read_text(encoding="utf-8")
    else:
        text = sys.stdin.read()

    result = assess_text(text)
    if args.json:
        print(json.dumps(result, indent=2))
    else:
        print(f"length_chars:           {result['length_chars']}")
        print(f"fallacy_total:          {result['fallacy_total']}")
        print(f"fallacy_density_score:  {result['fallacy_density_score']}")
        print(f"c3_score:               {result['c3_score']}")
        for name, count in result["fallacy_counts"].items():
            if count:
                print(f"  {name}: {count}")

    if args.annotate:
        annotated, _ = annotate_text(text)
        print("\n--- annotated ---")
        print(annotated)
    return 0


if __name__ == "__main__":
    sys.exit(_main())
