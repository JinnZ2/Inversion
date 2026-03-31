#!/usr/bin/env python3
"""
Contamination Detector — Quantitative Text Analysis

Analyzes text for structural properties that correlate with institutional
capture and epistemic degradation. Uses five quantitative metrics rather
than keyword matching:

  1. Lexical Diversity (MATTR)  — Moving-Average Type-Token Ratio
  2. Epistemic Hedging Ratio    — hedge words vs. assertive words
  3. Source Diversity            — citation count and entropy
  4. Argument Density            — premise-conclusion pair ratio
  5. Circular Reasoning Score   — Jaccard similarity between premises & conclusions

Each metric is individually reported with its value and interpretation.
The composite score combines all five on a [0, 1] scale.

References:
  - Covington & McFall (2010): MATTR for lexical diversity
  - Hyland (1998): hedging in academic discourse
  - Jaccard (1912): similarity coefficient
  - Shannon (1948): entropy for source concentration
"""

from __future__ import annotations

import argparse
import json
import math
import re
import string
import sys
from dataclasses import dataclass, field


# ---------------------------------------------------------------------------
# Tokenization
# ---------------------------------------------------------------------------

_PUNCT_TABLE = str.maketrans("", "", string.punctuation)


def tokenize(text: str) -> list[str]:
    """Lowercase, strip punctuation, split on whitespace."""
    return [w for w in text.lower().translate(_PUNCT_TABLE).split() if w]


def sentencize(text: str) -> list[str]:
    """Split text into sentences (simple heuristic)."""
    # Split on period/question/exclamation followed by space+capital or end
    parts = re.split(r'(?<=[.!?])\s+(?=[A-Z])', text)
    return [s.strip() for s in parts if s.strip()]


# ---------------------------------------------------------------------------
# Stopwords (minimal set for content-word extraction)
# ---------------------------------------------------------------------------

STOPWORDS = frozenset(
    "a an the and or but if in on at to for of is are was were be been being "
    "have has had do does did will would shall should can could may might must "
    "this that these those it its he she they we you i my your his her their "
    "our with from by as not no nor so yet also very too than then there here "
    "what which who whom whose when where how all each every some any many much "
    "more most other another such only just about above below between into "
    "through during before after".split()
)


def content_words(text: str) -> set[str]:
    """Extract content words (non-stopwords, length > 3)."""
    return {w for w in tokenize(text) if w not in STOPWORDS and len(w) > 3}


# ---------------------------------------------------------------------------
# Metric 1: Lexical Diversity — MATTR
# ---------------------------------------------------------------------------

def compute_mattr(tokens: list[str], window: int = 50) -> float:
    """
    Moving-Average Type-Token Ratio (Covington & McFall, 2010).

    Computes TTR over a sliding window and averages. This corrects for
    the text-length bias of raw TTR.

    Returns value in [0, 1]. Higher = more lexically diverse.
    """
    if len(tokens) < window:
        if not tokens:
            return 0.0
        return len(set(tokens)) / len(tokens)

    ttrs: list[float] = []
    for i in range(len(tokens) - window + 1):
        w = tokens[i : i + window]
        ttrs.append(len(set(w)) / window)
    return sum(ttrs) / len(ttrs)


# ---------------------------------------------------------------------------
# Metric 2: Epistemic Hedging Ratio
# ---------------------------------------------------------------------------

HEDGE_WORDS = [
    "might", "could", "possibly", "suggests", "appears", "seems",
    "arguably", "perhaps", "may", "likely", "unlikely", "approximately",
    "roughly", "tends", "sometimes", "often", "generally", "typically",
    "probably", "plausibly", "potentially", "conceivably",
]

ASSERTIVE_WORDS = [
    "clearly", "obviously", "undeniably", "certainly", "always", "never",
    "proven", "definitively", "unquestionably", "absolutely", "must",
    "guaranteed", "indisputable", "undoubtedly", "irrefutable",
    "incontrovertible", "without question", "beyond doubt",
]


def compute_hedging_ratio(tokens: list[str]) -> tuple[float, int, int]:
    """
    Ratio of hedging language to total epistemic markers.

    Healthy scientific text: 0.3–0.6 (Hyland 1998).
    Below 0.15: low epistemic humility — high assertiveness.
    Above 0.8: excessive hedging — may lack substance.

    Returns (ratio, hedge_count, assert_count).
    """
    text_joined = " ".join(tokens)
    hedge_count = sum(text_joined.count(h) for h in HEDGE_WORDS)
    assert_count = sum(text_joined.count(a) for a in ASSERTIVE_WORDS)
    total = hedge_count + assert_count
    if total == 0:
        return 0.5, 0, 0  # neutral if no epistemic markers
    return hedge_count / total, hedge_count, assert_count


# ---------------------------------------------------------------------------
# Metric 3: Source Diversity
# ---------------------------------------------------------------------------

CITATION_PATTERNS = [
    re.compile(r"\(([A-Z][a-z]+(?:\s+(?:et\s+al|&\s+[A-Z][a-z]+))?\.?,?\s*\d{4})\)"),  # (Author 2024)
    re.compile(r"\[(\d+)\]"),                          # [1]
    re.compile(r"https?://\S+"),                       # URLs
    re.compile(r"[Aa]ccording\s+to\s+([A-Z][^\.,]+)"),  # According to X
]


def compute_source_diversity(text: str) -> tuple[float, int, float]:
    """
    Analyze citation patterns in text.

    Returns:
      - source_density: unique_sources / paragraph_count
      - unique_source_count
      - source_entropy: Shannon entropy over source frequencies (bits)
    """
    paragraphs = [p.strip() for p in text.split("\n\n") if p.strip()]
    n_paragraphs = max(len(paragraphs), 1)

    sources: list[str] = []
    for pattern in CITATION_PATTERNS:
        for match in pattern.finditer(text):
            sources.append(match.group(0).lower().strip())

    unique = set(sources)
    n_unique = len(unique)
    source_density = n_unique / n_paragraphs

    # Shannon entropy over source frequencies
    if not sources:
        return source_density, 0, 0.0
    from collections import Counter
    counts = Counter(sources)
    total = len(sources)
    entropy = -sum((c / total) * math.log2(c / total) for c in counts.values())

    return source_density, n_unique, entropy


# ---------------------------------------------------------------------------
# Metric 4: Argument Density
# ---------------------------------------------------------------------------

PREMISE_INDICATORS = [
    "because", "since", "given that", "as evidenced by",
    "the reason is", "due to", "on the grounds that",
    "supported by", "as shown by", "the evidence shows",
]

CONCLUSION_INDICATORS = [
    "therefore", "thus", "hence", "consequently",
    "it follows that", "this means", "we can conclude",
    "this shows", "this demonstrates", "this implies",
    "as a result", "accordingly",
]


def compute_argument_density(sentences: list[str]) -> tuple[float, int]:
    """
    Ratio of premise-conclusion pairs to total sentences.

    Measures how much of the text is structured argumentation vs.
    bare assertion. Scientific text typically > 0.1.

    Returns (density, pair_count).
    """
    if not sentences:
        return 0.0, 0

    premise_indices: list[int] = []
    conclusion_indices: list[int] = []

    for i, sent in enumerate(sentences):
        lower = sent.lower()
        if any(ind in lower for ind in PREMISE_INDICATORS):
            premise_indices.append(i)
        if any(ind in lower for ind in CONCLUSION_INDICATORS):
            conclusion_indices.append(i)

    # Count valid premise-conclusion pairs (premise before conclusion, within 5 sentences)
    pairs = 0
    for ci in conclusion_indices:
        for pi in premise_indices:
            if 0 < ci - pi <= 5:
                pairs += 1
                break  # one match per conclusion

    return pairs / len(sentences), pairs


# ---------------------------------------------------------------------------
# Metric 5: Circular Reasoning Detection
# ---------------------------------------------------------------------------

def compute_circular_reasoning(sentences: list[str]) -> tuple[float, list[tuple[int, int, float]]]:
    """
    Detect circular reasoning via Jaccard similarity between premise
    and conclusion content words.

    For each conclusion sentence, find the nearest preceding premise.
    If the Jaccard similarity of their content words exceeds 0.5,
    flag as potential circular reasoning.

    Returns (score, list of (premise_idx, conclusion_idx, jaccard)).
    """
    if not sentences:
        return 0.0, []

    premise_map: dict[int, set[str]] = {}
    conclusion_map: dict[int, set[str]] = {}

    for i, sent in enumerate(sentences):
        lower = sent.lower()
        if any(ind in lower for ind in PREMISE_INDICATORS):
            premise_map[i] = content_words(sent)
        if any(ind in lower for ind in CONCLUSION_INDICATORS):
            conclusion_map[i] = content_words(sent)

    circular_pairs: list[tuple[int, int, float]] = []

    for ci, c_words in conclusion_map.items():
        if not c_words:
            continue
        # Find nearest preceding premise
        best_pi = -1
        best_jaccard = 0.0
        for pi, p_words in premise_map.items():
            if pi >= ci or not p_words:
                continue
            intersection = len(c_words & p_words)
            union = len(c_words | p_words)
            jaccard = intersection / union if union > 0 else 0.0
            if jaccard > best_jaccard:
                best_jaccard = jaccard
                best_pi = pi

        if best_pi >= 0 and best_jaccard > 0.5:
            circular_pairs.append((best_pi, ci, best_jaccard))

    n_conclusions = max(len(conclusion_map), 1)
    score = len(circular_pairs) / n_conclusions
    return score, circular_pairs


# ---------------------------------------------------------------------------
# Composite Report
# ---------------------------------------------------------------------------

@dataclass
class MetricResult:
    """Result of a single metric computation."""
    name: str
    value: float
    interpretation: str
    details: dict = field(default_factory=dict)


@dataclass
class Report:
    """Full analysis report."""
    source: str
    total_lines: int
    total_tokens: int
    total_sentences: int
    metrics: list[MetricResult] = field(default_factory=list)
    composite_score: float = 0.0
    risk_level: str = "CLEAN"


def clamp(x: float, lo: float = 0.0, hi: float = 1.0) -> float:
    return max(lo, min(hi, x))


def interpret_mattr(v: float) -> str:
    if v >= 0.70:
        return "HIGH lexical diversity — varied vocabulary"
    elif v >= 0.50:
        return "MODERATE lexical diversity — typical range"
    else:
        return "LOW lexical diversity — repetitive, formulaic language"


def interpret_hedging(v: float) -> str:
    if v < 0.15:
        return "VERY LOW epistemic humility — almost exclusively absolute claims"
    elif v < 0.30:
        return "LOW hedging — more assertive than typical scientific discourse"
    elif v <= 0.60:
        return "NORMAL hedging ratio — consistent with scientific discourse (Hyland 1998)"
    else:
        return "HIGH hedging — excessive qualification, may lack substance"


def interpret_argument_density(v: float) -> str:
    if v >= 0.10:
        return "ADEQUATE argument structure — claims supported by reasoning"
    elif v >= 0.05:
        return "LOW argument density — many unsupported assertions"
    else:
        return "VERY LOW — almost no structured argumentation detected"


def analyze(text: str, source: str = "<stdin>", sensor_import: object = None) -> Report:
    """Run all metrics and produce a composite report.

    If sensor_import (from fieldlink.parse_sensor_import) is provided,
    a sixth metric — Sensor Coherence — is added, measuring alignment
    between the text's epistemic signals and the somatic sensor atlas.
    """
    tokens = tokenize(text)
    sentences = sentencize(text)

    report = Report(
        source=source,
        total_lines=text.count("\n") + 1,
        total_tokens=len(tokens),
        total_sentences=len(sentences),
    )

    # 1. MATTR
    mattr = compute_mattr(tokens, window=50)
    report.metrics.append(MetricResult(
        name="Lexical Diversity (MATTR-50)",
        value=round(mattr, 4),
        interpretation=interpret_mattr(mattr),
        details={"window": 50, "total_tokens": len(tokens)},
    ))

    # 2. Hedging ratio
    hedging, n_hedge, n_assert = compute_hedging_ratio(tokens)
    report.metrics.append(MetricResult(
        name="Epistemic Hedging Ratio",
        value=round(hedging, 4),
        interpretation=interpret_hedging(hedging),
        details={"hedge_count": n_hedge, "assertive_count": n_assert},
    ))

    # 3. Source diversity
    src_density, n_sources, src_entropy = compute_source_diversity(text)
    report.metrics.append(MetricResult(
        name="Source Diversity",
        value=round(src_density, 4),
        interpretation=(
            f"{n_sources} unique source(s), density={src_density:.2f}/paragraph, "
            f"entropy={src_entropy:.2f} bits"
        ),
        details={
            "unique_sources": n_sources,
            "density": round(src_density, 4),
            "entropy_bits": round(src_entropy, 4),
        },
    ))

    # 4. Argument density
    arg_density, n_pairs = compute_argument_density(sentences)
    report.metrics.append(MetricResult(
        name="Argument Density",
        value=round(arg_density, 4),
        interpretation=interpret_argument_density(arg_density),
        details={"premise_conclusion_pairs": n_pairs, "total_sentences": len(sentences)},
    ))

    # 5. Circular reasoning
    circ_score, circ_pairs = compute_circular_reasoning(sentences)
    report.metrics.append(MetricResult(
        name="Circular Reasoning Score",
        value=round(circ_score, 4),
        interpretation=(
            f"{len(circ_pairs)} circular pair(s) detected"
            + (f" (max Jaccard={max(j for _, _, j in circ_pairs):.2f})" if circ_pairs else "")
        ),
        details={
            "circular_pairs": [
                {"premise_sentence": p, "conclusion_sentence": c, "jaccard": round(j, 4)}
                for p, c, j in circ_pairs
            ],
        },
    ))

    # 6. Sensor coherence (optional — requires fieldlink sensor import)
    sensor_concern = 0.0
    has_sensor = False
    if sensor_import is not None:
        try:
            from scripts.fieldlink import compute_sensor_coherence
            coherence = compute_sensor_coherence(text, sensor_import)
            sensor_score = coherence["coherence_score"]
            report.metrics.append(MetricResult(
                name="Sensor Coherence (fieldlink)",
                value=round(sensor_score, 4),
                interpretation=(
                    f"Coherence with somatic sensor atlas: {sensor_score:.2f} "
                    f"({coherence['n_sensors_matched']} sensors matched, "
                    f"{coherence['n_corruption_matches']} corruption flags)"
                ),
                details=coherence,
            ))
            sensor_concern = 1.0 - clamp(sensor_score)  # low coherence is concerning
            has_sensor = True
        except ImportError:
            pass  # fieldlink not available, skip gracefully

    # Composite score: higher = more contamination signals
    # Each component maps a metric to a [0,1] "concern" value
    mattr_concern = 1.0 - clamp(mattr / 0.70)           # low diversity is concerning
    hedging_concern = 1.0 - clamp(hedging / 0.50)        # low hedging is concerning
    arg_concern = 1.0 - clamp(arg_density / 0.10)        # low argument density is concerning
    src_concern = 1.0 - clamp(src_density / 0.50)        # low source density is concerning
    circ_concern = clamp(circ_score)                      # circular reasoning is concerning

    if has_sensor:
        # With sensor data: redistribute weights to include sensor coherence
        report.composite_score = round(
            0.20 * hedging_concern
            + 0.17 * mattr_concern
            + 0.17 * arg_concern
            + 0.17 * circ_concern
            + 0.12 * src_concern
            + 0.17 * sensor_concern,
            4,
        )
    else:
        report.composite_score = round(
            0.25 * hedging_concern
            + 0.20 * mattr_concern
            + 0.20 * arg_concern
            + 0.20 * circ_concern
            + 0.15 * src_concern,
            4,
        )

    if report.composite_score < 0.20:
        report.risk_level = "LOW"
    elif report.composite_score < 0.45:
        report.risk_level = "MODERATE"
    elif report.composite_score < 0.70:
        report.risk_level = "HIGH"
    else:
        report.risk_level = "CRITICAL"

    return report


# ---------------------------------------------------------------------------
# Output
# ---------------------------------------------------------------------------

def print_report(report: Report) -> None:
    print("=" * 80)
    print("  QUANTITATIVE TEXT ANALYSIS REPORT")
    print(f"  Source: {report.source}")
    print(f"  Tokens: {report.total_tokens}  |  Sentences: {report.total_sentences}  |  Lines: {report.total_lines}")
    print("=" * 80)

    for m in report.metrics:
        print(f"\n  [{m.name}]")
        print(f"    Value: {m.value}")
        print(f"    {m.interpretation}")

    print(f"\n{'=' * 80}")
    print(f"  COMPOSITE SCORE: {report.composite_score:.4f}  [{report.risk_level}]")
    print(f"{'=' * 80}")
    print()
    print("  Score components (0 = no concern, 1 = high concern):")
    print(f"    Hedging deficit    (25%): {1.0 - clamp(report.metrics[1].value / 0.50):.3f}")
    print(f"    Lexical poverty    (20%): {1.0 - clamp(report.metrics[0].value / 0.70):.3f}")
    print(f"    Argument deficit   (20%): {1.0 - clamp(report.metrics[3].value / 0.10):.3f}")
    print(f"    Circular reasoning (20%): {clamp(report.metrics[4].value):.3f}")
    print(f"    Source deficit     (15%): {1.0 - clamp(report.metrics[2].details['density'] / 0.50):.3f}")
    print()


def print_json_report(report: Report) -> None:
    data = {
        "source": report.source,
        "total_tokens": report.total_tokens,
        "total_sentences": report.total_sentences,
        "composite_score": report.composite_score,
        "risk_level": report.risk_level,
        "metrics": [
            {
                "name": m.name,
                "value": m.value,
                "interpretation": m.interpretation,
                **m.details,
            }
            for m in report.metrics
        ],
    }
    print(json.dumps(data, indent=2))


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Quantitative text analysis for epistemic quality"
    )
    parser.add_argument("file", nargs="?", help="File to analyze (default: stdin)")
    parser.add_argument("--text", "-t", help="Inline text to analyze")
    parser.add_argument("--json", action="store_true", help="Output as JSON")
    parser.add_argument(
        "--sensors", metavar="PATH",
        help="Path to Emotions-as-Sensors JSON export for sensor-augmented analysis",
    )
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

    # Load sensor import if provided
    sensor_import = None
    if args.sensors:
        try:
            from scripts.fieldlink import parse_sensor_import
            with open(args.sensors) as sf:
                sensor_import = parse_sensor_import(json.load(sf))
        except (ImportError, FileNotFoundError) as e:
            print(f"Warning: Could not load sensor data: {e}", file=sys.stderr)

    report = analyze(text, source, sensor_import=sensor_import)

    if args.json:
        print_json_report(report)
    else:
        print_report(report)

    if report.risk_level in ("HIGH", "CRITICAL"):
        sys.exit(2)
    elif report.risk_level == "MODERATE":
        sys.exit(1)
    else:
        sys.exit(0)


if __name__ == "__main__":
    main()
