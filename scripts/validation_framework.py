#!/usr/bin/env python3
"""
Multi-Epistemological Validation Framework — Quantitative Edition

Validates claims using information-theoretic and structural metrics
rather than keyword matching:

  1. Information Entropy     — character & word-level Shannon entropy, compressibility
  2. Falsifiability Score    — quantifier specificity, temporal grounding, measurability
  3. Internal Consistency    — relation extraction and sign-consistency checking
  4. Citation Analysis       — source concentration, age distribution, authority entropy
  5. Cross-Domain Score      — probabilistic aggregation across all domains

References:
  - Shannon (1948): information entropy
  - Popper (1959): falsifiability as demarcation criterion
  - Normalized Compression Distance: Cilibrasi & Vitanyi (2005)
  - Kolmogorov complexity approximation via zlib: Li et al. (2004)
"""

from __future__ import annotations

import argparse
import json
import math
import re
import string
import sys
import zlib
from collections import Counter
from dataclasses import dataclass, field


# ---------------------------------------------------------------------------
# Tokenization helpers
# ---------------------------------------------------------------------------

_PUNCT_TABLE = str.maketrans("", "", string.punctuation)


def tokenize(text: str) -> list[str]:
    return [w for w in text.lower().translate(_PUNCT_TABLE).split() if w]


def sentencize(text: str) -> list[str]:
    parts = re.split(r'(?<=[.!?])\s+(?=[A-Z])', text)
    return [s.strip() for s in parts if s.strip()]


# ---------------------------------------------------------------------------
# Metric 1: Information Entropy & Compressibility
# ---------------------------------------------------------------------------

def char_entropy(text: str) -> float:
    """Shannon entropy over character distribution (bits)."""
    if not text:
        return 0.0
    counts = Counter(text.lower())
    total = len(text)
    return -sum((c / total) * math.log2(c / total) for c in counts.values())


def word_entropy(tokens: list[str]) -> float:
    """Shannon entropy over word distribution (bits)."""
    if not tokens:
        return 0.0
    counts = Counter(tokens)
    total = len(tokens)
    return -sum((c / total) * math.log2(c / total) for c in counts.values())


def compressibility(text: str) -> float:
    """
    Compression ratio as a proxy for Kolmogorov complexity.
    Uses zlib (stdlib). Higher = more compressible = more redundant.

    Based on Normalized Compression Distance literature
    (Cilibrasi & Vitanyi 2005).
    """
    if not text:
        return 0.0
    original = text.encode("utf-8")
    compressed = zlib.compress(original, 9)
    return 1.0 - len(compressed) / len(original)


@dataclass
class EntropyResult:
    char_entropy_bits: float       # typical English: 4.0–4.5
    word_entropy_bits: float
    compressibility_ratio: float   # 0 = incompressible, 1 = fully redundant
    interpretation: str


def analyze_entropy(text: str, tokens: list[str]) -> EntropyResult:
    h_char = char_entropy(text)
    h_word = word_entropy(tokens)
    comp = compressibility(text)

    issues = []
    if h_char < 3.0:
        issues.append("very low character entropy (highly repetitive)")
    if h_char > 4.8:
        issues.append("unusually high character entropy (possibly random/encoded)")
    if comp > 0.7:
        issues.append(f"high compressibility ({comp:.0%}) — low information density")

    return EntropyResult(
        char_entropy_bits=round(h_char, 4),
        word_entropy_bits=round(h_word, 4),
        compressibility_ratio=round(comp, 4),
        interpretation="; ".join(issues) if issues else "entropy within normal range",
    )


# ---------------------------------------------------------------------------
# Metric 2: Falsifiability Score
# ---------------------------------------------------------------------------

SPECIFIC_QUANTIFIERS = re.compile(
    r"\b\d+\.?\d*\s*%|\b\d+\.?\d*\b(?:\s*(?:times|fold|percent|kg|km|m|cm|mm|"
    r"hours?|days?|years?|months?|seconds?|million|billion|thousand))\b|"
    r"\bbetween\s+\d+\s+and\s+\d+\b|\bby\s+\d{4}\b|\bin\s+\d{4}\b",
    re.IGNORECASE,
)

VAGUE_QUANTIFIERS = re.compile(
    r"\b(many|most|some|various|significant|numerous|several|"
    r"few|substantial|considerable|a lot|a number of)\b",
    re.IGNORECASE,
)

TEMPORAL_SPECIFIC = re.compile(
    r"\b(in\s+\d{4}|by\s+\d{4}|within\s+\d+\s+\w+|"
    r"\d{1,2}/\d{1,2}/\d{2,4}|\d{4}-\d{2}|"
    r"between\s+\d{4}\s+and\s+\d{4}|from\s+\d{4}\s+to\s+\d{4}|"
    r"since\s+\d{4}|after\s+\d{4}|before\s+\d{4}|"
    r"next\s+\d+\s+\w+|over\s+\d+\s+\w+)\b",
    re.IGNORECASE,
)

TEMPORAL_VAGUE = re.compile(
    r"\b(always|never|inherently|by nature|eternally|"
    r"fundamentally|inevitably|permanently)\b",
    re.IGNORECASE,
)

MEASURABILITY_WORDS = re.compile(
    r"\b(measured|observed|counted|rate of|percentage|"
    r"correlation|statistically|empirically|quantified|"
    r"data shows|experiment|sample size|p-value|confidence interval)\b",
    re.IGNORECASE,
)

UNFALSIFIABLE_FRAMING = re.compile(
    r"\b(essentially|in principle|fundamentally|by definition|"
    r"it is known that|self-evidently|axiomatically|"
    r"it goes without saying|needless to say)\b",
    re.IGNORECASE,
)


@dataclass
class FalsifiabilityResult:
    score: float                  # [0, 1], higher = more falsifiable
    quantifier_specificity: float
    temporal_specificity: float
    measurability: float
    interpretation: str
    details: dict = field(default_factory=dict)


def analyze_falsifiability(text: str) -> FalsifiabilityResult:
    """
    Score how falsifiable a claim is based on structural properties.

    Based on Popper's demarcation criterion: a claim is scientific
    if it makes specific, testable, potentially refutable predictions.
    """
    n_specific_q = len(SPECIFIC_QUANTIFIERS.findall(text))
    n_vague_q = len(VAGUE_QUANTIFIERS.findall(text))
    quantifier_spec = n_specific_q / (n_specific_q + n_vague_q + 1)

    n_temporal_spec = len(TEMPORAL_SPECIFIC.findall(text))
    n_temporal_vague = len(TEMPORAL_VAGUE.findall(text))
    temporal_spec = n_temporal_spec / (n_temporal_spec + n_temporal_vague + 1)

    n_measurable = len(MEASURABILITY_WORDS.findall(text))
    n_unfalsifiable = len(UNFALSIFIABLE_FRAMING.findall(text))
    measurability = n_measurable / (n_measurable + n_unfalsifiable + 1)

    score = (
        0.40 * quantifier_spec
        + 0.30 * measurability
        + 0.30 * temporal_spec
    )

    if score >= 0.40:
        interp = "FALSIFIABLE — contains specific, testable elements"
    elif score >= 0.20:
        interp = "PARTIALLY FALSIFIABLE — some specificity, could be more testable"
    else:
        interp = "LOW FALSIFIABILITY — vague, hard to test or refute"

    return FalsifiabilityResult(
        score=round(score, 4),
        quantifier_specificity=round(quantifier_spec, 4),
        temporal_specificity=round(temporal_spec, 4),
        measurability=round(measurability, 4),
        interpretation=interp,
        details={
            "specific_quantifiers": n_specific_q,
            "vague_quantifiers": n_vague_q,
            "temporal_specific": n_temporal_spec,
            "temporal_vague": n_temporal_vague,
            "measurability_markers": n_measurable,
            "unfalsifiable_markers": n_unfalsifiable,
        },
    )


# ---------------------------------------------------------------------------
# Metric 3: Internal Consistency
# ---------------------------------------------------------------------------

POSITIVE_PREDICATES = re.compile(
    r"\b(increases?|causes?|leads?\s+to|improves?|promotes?|"
    r"enables?|produces?|creates?|enhances?|strengthens?)\b",
    re.IGNORECASE,
)

NEGATIVE_PREDICATES = re.compile(
    r"\b(decreases?|reduces?|prevents?|harms?|inhibits?|"
    r"destroys?|weakens?|eliminates?|undermines?|blocks?)\b",
    re.IGNORECASE,
)


@dataclass
class Relation:
    subject: str
    direction: int  # +1 or -1
    obj: str
    sentence_idx: int


@dataclass
class ConsistencyResult:
    score: float              # [0, 1], higher = more consistent
    relations_found: int
    contradictions: list[tuple[str, str]]  # pairs of contradictory sentences
    interpretation: str


def extract_relations(sentences: list[str]) -> list[Relation]:
    """
    Extract subject-predicate-object relations from simple sentence structures.
    Looks for patterns like "X increases Y" or "X leads to Y".
    """
    relations: list[Relation] = []
    for idx, sent in enumerate(sentences):
        # Try positive predicates
        for m in POSITIVE_PREDICATES.finditer(sent):
            before = sent[:m.start()].strip().split()[-3:]  # last 3 words as subject
            after = sent[m.end():].strip().split()[:3]       # first 3 words as object
            if before and after:
                relations.append(Relation(
                    subject=" ".join(before).lower().strip(string.punctuation),
                    direction=1,
                    obj=" ".join(after).lower().strip(string.punctuation),
                    sentence_idx=idx,
                ))
        # Try negative predicates
        for m in NEGATIVE_PREDICATES.finditer(sent):
            before = sent[:m.start()].strip().split()[-3:]
            after = sent[m.end():].strip().split()[:3]
            if before and after:
                relations.append(Relation(
                    subject=" ".join(before).lower().strip(string.punctuation),
                    direction=-1,
                    obj=" ".join(after).lower().strip(string.punctuation),
                    sentence_idx=idx,
                ))
    return relations


def check_consistency(sentences: list[str]) -> ConsistencyResult:
    """
    Check for direct contradictions: same subject-object pair with
    opposite direction predicates.
    """
    relations = extract_relations(sentences)
    if not relations:
        return ConsistencyResult(
            score=1.0, relations_found=0, contradictions=[],
            interpretation="No extractable relations — cannot assess consistency",
        )

    # Group by (subject, object) pair
    pairs: dict[tuple[str, str], list[Relation]] = {}
    for r in relations:
        key = (r.subject, r.obj)
        pairs.setdefault(key, []).append(r)

    contradictions: list[tuple[str, str]] = []
    for (subj, obj), rels in pairs.items():
        directions = {r.direction for r in rels}
        if len(directions) > 1:  # both +1 and -1
            s1 = sentences[rels[0].sentence_idx][:80]
            s2 = next(sentences[r.sentence_idx][:80] for r in rels if r.direction != rels[0].direction)
            contradictions.append((s1, s2))

    n_pairs = len(pairs)
    n_contradictions = len(contradictions)
    score = 1.0 - (n_contradictions / max(n_pairs, 1))

    if n_contradictions == 0:
        interp = "CONSISTENT — no direct contradictions detected"
    elif n_contradictions <= 2:
        interp = f"MINOR INCONSISTENCY — {n_contradictions} contradiction(s)"
    else:
        interp = f"INCONSISTENT — {n_contradictions} contradictions in {n_pairs} relation pairs"

    return ConsistencyResult(
        score=round(max(0.0, score), 4),
        relations_found=len(relations),
        contradictions=contradictions,
        interpretation=interp,
    )


# ---------------------------------------------------------------------------
# Metric 4: Citation Analysis
# ---------------------------------------------------------------------------

CITATION_AUTHOR = re.compile(r"\(([A-Z][a-z]+(?:\s+(?:et\s+al|&\s+[A-Z][a-z]+))?)[.,]?\s*(\d{4})\)")
CITATION_YEAR = re.compile(r"\b((?:19|20)\d{2})\b")


@dataclass
class CitationResult:
    citation_count: int
    unique_authors: int
    author_entropy: float          # Shannon entropy over cited authors (bits)
    mean_citation_age: float       # years from current year
    citation_to_sentence_ratio: float
    interpretation: str


def analyze_citations(text: str, sentences: list[str], current_year: int = 2026) -> CitationResult:
    """Analyze citation patterns for authority concentration and currency."""
    author_matches = CITATION_AUTHOR.findall(text)
    authors = [a[0].lower() for a in author_matches]
    years = [int(a[1]) for a in author_matches]

    # Also count bare [N] style citations
    bracket_cites = re.findall(r"\[\d+\]", text)

    total_cites = len(authors) + len(bracket_cites)
    unique_auth = len(set(authors))

    # Author entropy
    if authors:
        counts = Counter(authors)
        total_a = len(authors)
        author_entropy = -sum((c / total_a) * math.log2(c / total_a) for c in counts.values())
    else:
        author_entropy = 0.0

    # Mean citation age
    if years:
        mean_age = sum(current_year - y for y in years) / len(years)
    else:
        mean_age = 0.0

    ratio = total_cites / max(len(sentences), 1)

    issues = []
    if total_cites == 0:
        issues.append("no citations found")
    elif unique_auth > 0 and author_entropy < 1.0:
        issues.append("low author diversity — possible authority concentration")
    if mean_age > 20:
        issues.append(f"mean citation age is {mean_age:.0f} years — evidence may be outdated")
    if ratio < 0.05 and len(sentences) > 5:
        issues.append("very low citation-to-sentence ratio for empirical claims")

    return CitationResult(
        citation_count=total_cites,
        unique_authors=unique_auth,
        author_entropy=round(author_entropy, 4),
        mean_citation_age=round(mean_age, 1),
        citation_to_sentence_ratio=round(ratio, 4),
        interpretation="; ".join(issues) if issues else "citation profile within normal range",
    )


# ---------------------------------------------------------------------------
# Cross-Domain Aggregation
# ---------------------------------------------------------------------------

@dataclass
class DomainScore:
    name: str
    score: float          # [0, 1], higher = more concern
    interpretation: str


@dataclass
class ValidationReport:
    claim: str
    entropy: EntropyResult
    falsifiability: FalsifiabilityResult
    consistency: ConsistencyResult
    citations: CitationResult
    domain_scores: list[DomainScore]
    overall_concern: float    # [0, 1]
    interpretation: str


def clamp(x: float, lo: float = 0.0, hi: float = 1.0) -> float:
    return max(lo, min(hi, x))


def validate_claim(text: str, sensor_import: object = None) -> ValidationReport:
    """Run all analyses and produce a cross-domain validation report.

    If sensor_import (from fieldlink.parse_sensor_import) is provided,
    a fifth domain — Somatic Alignment — is added to the cross-domain
    scoring, measuring consistency with the body's evolved sensing
    apparatus as mapped by the Emotions-as-Sensors sensor atlas.
    """
    tokens = tokenize(text)
    sentences = sentencize(text)

    entropy = analyze_entropy(text, tokens)
    falsifiability = analyze_falsifiability(text)
    consistency = check_consistency(sentences)
    citations = analyze_citations(text, sentences)

    # Map metrics to domain concern scores [0, 1]
    domains = []

    # Physics/Thermodynamics: concerned about unfalsifiable claims with high compressibility
    phys_concern = (
        0.5 * (1.0 - clamp(falsifiability.score / 0.4))
        + 0.5 * clamp(entropy.compressibility_ratio / 0.6)
    )
    domains.append(DomainScore(
        "Physics / Thermodynamics", round(phys_concern, 4),
        "Assesses whether claims are thermodynamically plausible and testable",
    ))

    # Biology/Evolution: concerned about low falsifiability + no temporal grounding
    bio_concern = (
        0.6 * (1.0 - clamp(falsifiability.score / 0.4))
        + 0.4 * (1.0 - clamp(falsifiability.temporal_specificity / 0.3))
    )
    domains.append(DomainScore(
        "Biology / Evolution", round(bio_concern, 4),
        "Assesses whether claims about living systems are grounded and testable",
    ))

    # Systems Dynamics: concerned about inconsistency + low information content
    sys_concern = (
        0.5 * (1.0 - clamp(consistency.score))
        + 0.5 * clamp(entropy.compressibility_ratio / 0.5)
    )
    domains.append(DomainScore(
        "Systems Dynamics", round(sys_concern, 4),
        "Assesses internal consistency and information density of systems claims",
    ))

    # Empirical Observation: concerned about citation gaps + unfalsifiability
    emp_concern = (
        0.4 * (1.0 - clamp(citations.citation_to_sentence_ratio / 0.1))
        + 0.3 * (1.0 - clamp(falsifiability.measurability / 0.3))
        + 0.3 * (1.0 - clamp(citations.author_entropy / 2.0))
    )
    domains.append(DomainScore(
        "Empirical Observation", round(emp_concern, 4),
        "Assesses evidence base, citation quality, and measurability",
    ))

    # 5. Somatic Alignment (optional — requires fieldlink sensor import)
    if sensor_import is not None:
        try:
            from scripts.fieldlink import compute_somatic_alignment
            somatic = compute_somatic_alignment(text, sensor_import)
            domains.append(DomainScore(
                "Somatic Alignment", round(somatic["concern"], 4),
                somatic["interpretation"],
            ))
        except ImportError:
            pass  # fieldlink not available, skip gracefully

    # Aggregate: weighted mean of domain scores, with a boost if multiple domains flag
    mean_score = sum(d.score for d in domains) / len(domains)
    n_flagged = sum(1 for d in domains if d.score > 0.5)
    # Multi-domain boost: if 3+ domains flag, escalate
    multi_boost = 0.1 * max(0, n_flagged - 2)
    overall = round(clamp(mean_score + multi_boost), 4)

    if overall < 0.25:
        interp = "LOW CONCERN — claim structure appears epistemically sound"
    elif overall < 0.50:
        interp = "MODERATE CONCERN — some structural weaknesses in claim"
    elif overall < 0.70:
        interp = "HIGH CONCERN — multiple epistemic red flags"
    else:
        interp = "VERY HIGH CONCERN — claim fails multiple validation dimensions"

    return ValidationReport(
        claim=text,
        entropy=entropy,
        falsifiability=falsifiability,
        consistency=consistency,
        citations=citations,
        domain_scores=domains,
        overall_concern=overall,
        interpretation=interp,
    )


# ---------------------------------------------------------------------------
# Output
# ---------------------------------------------------------------------------

def print_report(report: ValidationReport) -> None:
    print("=" * 80)
    print("  MULTI-EPISTEMOLOGICAL VALIDATION REPORT")
    print("=" * 80)

    claim_display = report.claim[:200] + "..." if len(report.claim) > 200 else report.claim
    print(f"\n  Claim: \"{claim_display}\"\n")

    # Entropy
    e = report.entropy
    print(f"  [1] Information Entropy")
    print(f"      Character entropy:  {e.char_entropy_bits:.4f} bits  (English typical: 4.0–4.5)")
    print(f"      Word entropy:       {e.word_entropy_bits:.4f} bits")
    print(f"      Compressibility:    {e.compressibility_ratio:.4f}  (zlib proxy for Kolmogorov complexity)")
    print(f"      {e.interpretation}")

    # Falsifiability
    f = report.falsifiability
    print(f"\n  [2] Falsifiability (Popper 1959)")
    print(f"      Overall score:      {f.score:.4f}  [0=unfalsifiable, 1=highly testable]")
    print(f"      Quantifier spec:    {f.quantifier_specificity:.4f}  ({f.details['specific_quantifiers']} specific / {f.details['vague_quantifiers']} vague)")
    print(f"      Temporal grounding: {f.temporal_specificity:.4f}  ({f.details['temporal_specific']} specific / {f.details['temporal_vague']} vague)")
    print(f"      Measurability:      {f.measurability:.4f}  ({f.details['measurability_markers']} markers / {f.details['unfalsifiable_markers']} unfalsifiable)")
    print(f"      {f.interpretation}")

    # Consistency
    c = report.consistency
    print(f"\n  [3] Internal Consistency")
    print(f"      Score:              {c.score:.4f}  [0=contradictory, 1=consistent]")
    print(f"      Relations extracted: {c.relations_found}")
    if c.contradictions:
        print(f"      Contradictions ({len(c.contradictions)}):")
        for s1, s2 in c.contradictions[:3]:
            print(f"        \"{s1}...\"")
            print(f"        vs \"{s2}...\"")
    print(f"      {c.interpretation}")

    # Citations
    ci = report.citations
    print(f"\n  [4] Citation Analysis")
    print(f"      Total citations:    {ci.citation_count}")
    print(f"      Unique authors:     {ci.unique_authors}")
    print(f"      Author entropy:     {ci.author_entropy:.4f} bits  (higher = more diverse)")
    print(f"      Mean citation age:  {ci.mean_citation_age:.1f} years")
    print(f"      Cite/sentence ratio: {ci.citation_to_sentence_ratio:.4f}")
    print(f"      {ci.interpretation}")

    # Domain scores
    print(f"\n  [5] Cross-Domain Concern Scores")
    for d in report.domain_scores:
        bar = "#" * int(d.score * 20) + "." * (20 - int(d.score * 20))
        print(f"      [{bar}] {d.score:.4f}  {d.name}")

    print(f"\n{'=' * 80}")
    print(f"  OVERALL: {report.overall_concern:.4f}  —  {report.interpretation}")
    print(f"  Aggregation: mean(domain_scores) + multi-domain boost")
    print(f"{'=' * 80}\n")


def print_json_report(report: ValidationReport) -> None:
    data = {
        "claim": report.claim[:500],
        "overall_concern": report.overall_concern,
        "interpretation": report.interpretation,
        "entropy": {
            "char_bits": report.entropy.char_entropy_bits,
            "word_bits": report.entropy.word_entropy_bits,
            "compressibility": report.entropy.compressibility_ratio,
        },
        "falsifiability": {
            "score": report.falsifiability.score,
            "quantifier_specificity": report.falsifiability.quantifier_specificity,
            "temporal_specificity": report.falsifiability.temporal_specificity,
            "measurability": report.falsifiability.measurability,
            **report.falsifiability.details,
        },
        "consistency": {
            "score": report.consistency.score,
            "relations_found": report.consistency.relations_found,
            "contradictions": len(report.consistency.contradictions),
        },
        "citations": {
            "count": report.citations.citation_count,
            "unique_authors": report.citations.unique_authors,
            "author_entropy": report.citations.author_entropy,
            "mean_age": report.citations.mean_citation_age,
            "cite_sentence_ratio": report.citations.citation_to_sentence_ratio,
        },
        "domain_scores": {d.name: d.score for d in report.domain_scores},
    }
    print(json.dumps(data, indent=2))


def interactive_mode() -> None:
    print("=" * 80)
    print("  MULTI-EPISTEMOLOGICAL VALIDATION FRAMEWORK (Quantitative)")
    print("  Enter claims to validate (Ctrl+D or 'quit' to exit)")
    print("=" * 80)

    while True:
        try:
            claim = input("\n  Enter claim: ").strip()
        except (EOFError, KeyboardInterrupt):
            print()
            break
        if not claim or claim.lower() in ("quit", "exit", "q"):
            break
        report = validate_claim(claim)
        print()
        print_report(report)


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Quantitative multi-epistemological claim validation"
    )
    parser.add_argument("--claim", "-c", help="Single claim to validate")
    parser.add_argument("--file", "-f", help="File to validate (full text)")
    parser.add_argument("--json", action="store_true", help="Output as JSON")
    parser.add_argument(
        "--sensors", metavar="PATH",
        help="Path to Emotions-as-Sensors JSON export for somatic alignment scoring",
    )
    args = parser.parse_args()

    # Load sensor import if provided
    sensor_import = None
    if args.sensors:
        try:
            from scripts.fieldlink import parse_sensor_import
            with open(args.sensors) as sf:
                sensor_import = parse_sensor_import(json.load(sf))
        except (ImportError, FileNotFoundError) as e:
            print(f"Warning: Could not load sensor data: {e}", file=sys.stderr)

    if args.claim:
        report = validate_claim(args.claim, sensor_import=sensor_import)
        (print_json_report if args.json else print_report)(report)
    elif args.file:
        with open(args.file) as f:
            text = f.read()
        report = validate_claim(text, sensor_import=sensor_import)
        (print_json_report if args.json else print_report)(report)
    else:
        interactive_mode()


if __name__ == "__main__":
    main()
