#!/usr/bin/env python3
"""
logic_ferret.py -- Fallacy annotation + full seven-sensor composite C3 score.

Vendored and consolidated from:
    https://github.com/JinnZ2/Logic-Ferret

Upstream module map (all MIT, relicensed CC0 here to match the Inversion
repository; attribution preserved):

    sensor_suite/sensors/fallacy_overlay.py       -> annotate_text / FALLACY_PATTERNS
    sensor_suite/sensors/propaganda_tone.py       -> sensor_propaganda_tone
    sensor_suite/sensors/reward_manipulation.py   -> sensor_reward_manipulation
    sensor_suite/sensors/false_urgency.py         -> sensor_false_urgency
    sensor_suite/sensors/gatekeeping_sensor.py    -> sensor_gatekeeping
    sensor_suite/sensors/narrative_fragility.py   -> sensor_narrative_fragility
    sensor_suite/sensors/propaganda_bias.py       -> sensor_propaganda_bias
    sensor_suite/sensors/agency_detector.py       -> sensor_agency
    sensor_suite/sensors/truth_integrity_score.py -> calculate_c3 (weighted aggregate)

Each sensor returns ``(score, flags)`` where ``score`` is in [0, 1] and
higher = more of the negative pattern. ``calculate_c3`` aggregates the
seven named sensors into a composite truth-integrity score (also in
[0, 1], higher = more corruption signal).

The ``fallacy_density_score`` is the inverse of that convention by
design: 1.0 = clean, 0.0 = saturated. Keep this in mind when reading
``assess_text`` output -- it surfaces both.
"""

from __future__ import annotations

import argparse
import json
import re
import sys
from pathlib import Path
from typing import Callable, Dict, Tuple


# ---------------------------------------------------------------------------
# FALLACY OVERLAY
# ---------------------------------------------------------------------------

FALLACY_PATTERNS: Dict[str, str] = {
    "Strawman": r"\b(so what you're saying is|let me get this straight)\b",
    "Ad Hominem": r"\b(you're just|you must be|only an idiot would)\b",
    "Slippery Slope": r"\b(if we allow this|what's next)\b",
    "Appeal to Emotion": r"\b(think of the children|how would you feel)\b",
    "False Dichotomy": r"\b(either.*or|you must choose)\b",
    "Circular Reasoning": r"\b(because I said so|it just is)\b",
    "Bandwagon": r"\b(everyone knows|obviously)\b",
}


def annotate_text(text: str) -> Tuple[str, Dict[str, int]]:
    """Wrap fallacy matches in [TAG] markers and return (annotated, counts)."""
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
    """1.0 = clean, 0.0 = >=10 fallacies per 1000 chars."""
    total = sum(counts.values())
    density = total / max(length_chars / 1000.0, 1.0)
    return max(0.0, 1.0 - min(density / 10.0, 1.0))


# ---------------------------------------------------------------------------
# SENSORS
# ---------------------------------------------------------------------------
# Each returns (score in [0,1], flags dict). Score convention: higher = worse.
# Phrase lists are direct copies of the upstream sensor modules.


def _proportion(hits: int, universe: int, weight: float) -> float:
    if universe <= 0:
        return 0.0
    return (hits * weight) / (universe * weight)


def sensor_propaganda_tone(text: str) -> Tuple[float, Dict[str, str]]:
    FRAMING_PHRASES = [
        "they don't want you to know", "wake up", "the truth is", "everything you know is a lie",
        "mainstream media", "puppet masters", "red pill", "patriots", "elite agenda",
    ]
    BINARY_OPPOSITIONS = ["us vs them", "good vs evil", "freedom vs control", "truth vs lies"]
    EMOTIONAL_WORDS = [
        "betrayal", "corrupt", "hero", "evil", "savior", "tyranny", "liberty", "war", "rigged",
    ]
    REPETITION_WARNINGS = ["wake up", "fight back", "the truth", "exposed", "the real story"]

    lower = text.lower()
    framing = sum(1 for p in FRAMING_PHRASES if p in lower)
    binary = sum(1 for p in BINARY_OPPOSITIONS if p in lower)
    emotional = sum(1 for w in EMOTIONAL_WORDS if re.search(rf"\b{w}\b", lower))
    repetition = sum(lower.count(p) for p in REPETITION_WARNINGS if lower.count(p) > 1)

    total_weight = (framing * 1.5) + (binary * 1.2) + emotional + (repetition * 1.3)
    total_possible = (
        len(FRAMING_PHRASES) * 1.5 + len(BINARY_OPPOSITIONS) * 1.2 + len(EMOTIONAL_WORDS) + len(REPETITION_WARNINGS) * 1.3
    )
    score = min(total_weight / total_possible, 1.0) if total_possible else 0.0
    return score, {
        "Framing Phrases Detected": str(framing),
        "Binary Logic Framing": str(binary),
        "Emotional Language Hits": str(emotional),
        "Repetitive Phrase Alerts": str(repetition),
        "Framing Index": f"{score:.3f}",
    }


def sensor_reward_manipulation(text: str) -> Tuple[float, Dict[str, str]]:
    FOMO_TRIGGERS = [
        "limited time", "last chance", "offer ends soon", "don't miss out",
        "only available today", "act now", "while supplies last", "exclusive access",
    ]
    SOCIAL_PROOF_PHRASES = [
        "join 10,000 others", "everyone's using", "most popular", "our top choice", "trending now",
    ]
    EMOTIONAL_BRIBES = [
        "you deserve", "you owe it to yourself", "real men", "real women", "true patriot", "prove you care",
    ]
    INSTANT_GRATIFICATION = [
        "right now", "immediately", "fastest", "instant access", "get results today",
    ]

    lower = text.lower()
    fomo = sum(1 for p in FOMO_TRIGGERS if p in lower)
    social = sum(1 for p in SOCIAL_PROOF_PHRASES if p in lower)
    bribe = sum(1 for p in EMOTIONAL_BRIBES if p in lower)
    grat = sum(1 for p in INSTANT_GRATIFICATION if p in lower)

    total_weight = (fomo * 1.5) + (social * 1.2) + (bribe * 1.3) + (grat * 1.4)
    total_possible = (
        len(FOMO_TRIGGERS) * 1.5 + len(SOCIAL_PROOF_PHRASES) * 1.2 + len(EMOTIONAL_BRIBES) * 1.3 + len(INSTANT_GRATIFICATION) * 1.4
    )
    score = min(total_weight / total_possible, 1.0) if total_possible else 0.0
    return score, {
        "FOMO Triggers": str(fomo),
        "Social Pressure Hooks": str(social),
        "Emotional Bribes": str(bribe),
        "Instant Gratification Promises": str(grat),
        "Dopamine Lure Score": f"{score:.3f}",
    }


def sensor_false_urgency(text: str) -> Tuple[float, Dict[str, str]]:
    HYPE_URGENCY = [
        "now", "immediately", "before it's too late", "today only", "act fast", "won't last",
        "right now", "time is running out", "before it's gone", "urgent", "deadline",
        "vanishing", "limited time", "final call",
    ]
    FAKE_COUNTDOWN = [
        r"ends in", r"only \d+ hours left", r"offer expires", r"sale ends soon",
        r"last chance", r"you have \d+ minutes", r"expiring soon",
    ]
    CRISIS_WORDS = [
        "collapse", "emergency", "meltdown", "grid down", "total failure", "shutdown",
        "economic implosion", "end of freedom",
    ]

    lower = text.lower()
    hype = sum(1 for p in HYPE_URGENCY if p in lower)
    crisis = sum(1 for w in CRISIS_WORDS if w in lower)
    countdown = len(re.findall(r"(\d{1,2})\s?(minutes|hours|days)", lower))
    countdown += sum(1 for p in FAKE_COUNTDOWN if re.search(p, lower))

    total_weight = (hype * 1.4) + (countdown * 1.6) + (crisis * 1.2)
    total_possible = len(HYPE_URGENCY) * 1.4 + len(FAKE_COUNTDOWN) * 1.6 + len(CRISIS_WORDS) * 1.2
    score = min(total_weight / total_possible, 1.0) if total_possible else 0.0
    return score, {
        "Hype Phrases": str(hype),
        "Crisis Language": str(crisis),
        "Time Constraint Triggers": str(countdown),
        "Urgency Realness Score": f"{score:.3f}",
    }


def sensor_gatekeeping(text: str) -> Tuple[float, Dict[str, str]]:
    CREDENTIALISM_PHRASES = [
        "as an expert", "only qualified professionals", "not for beginners",
        "must have a phd", "you wouldn't understand", "requires certification",
        "peer-reviewed only", "credentials required",
    ]
    TECH_JARGON = [
        "asymptotic", "orthogonal", "synergistic", "framework", "heuristic",
        "ontology", "interoperability", "quantization", "elasticity", "scalability",
    ]
    ACCESS_CONTROL_PHRASES = [
        "members only", "behind paywall", "subscribe to access", "exclusive content",
        "premium tier", "sign in to view", "confidential data", "nda required",
    ]

    lower = text.lower()
    cred = sum(1 for p in CREDENTIALISM_PHRASES if p in lower)
    jargon = sum(1 for t in TECH_JARGON if re.search(rf"\b{t}\b", lower))
    access = sum(1 for p in ACCESS_CONTROL_PHRASES if p in lower)

    total_weight = (cred * 1.3) + (jargon * 1.5) + (access * 1.4)
    total_possible = len(CREDENTIALISM_PHRASES) * 1.3 + len(TECH_JARGON) * 1.5 + len(ACCESS_CONTROL_PHRASES) * 1.4
    score = min(total_weight / total_possible, 1.0) if total_possible else 0.0
    return score, {
        "Credentialist Language": str(cred),
        "Jargon Density": str(jargon),
        "Access Restriction Phrases": str(access),
        "Gatekeeping Index": f"{score:.3f}",
    }


def sensor_narrative_fragility(text: str) -> Tuple[float, Dict[str, str]]:
    LOGICAL_CONNECTORS = ["therefore", "thus", "because", "as a result", "proves that", "means that"]
    WEAK_TRANSITIONS = ["some say", "it's believed", "many agree", "people are saying", "obviously", "clearly"]
    EVIDENCE_GAPS = ["no data", "unverified", "no evidence", "without proof", "allegedly"]
    ABSURD_EXTRAPOLATIONS = [
        "so the world must", "this means everything changes", "proves all", "changes everything",
    ]

    lower = text.lower()
    weak = sum(1 for p in WEAK_TRANSITIONS if p in lower)
    missing = sum(1 for p in EVIDENCE_GAPS if p in lower)
    sketchy = sum(1 for p in LOGICAL_CONNECTORS if re.search(rf"{p}\s+[a-z]", lower))
    wild = sum(1 for p in ABSURD_EXTRAPOLATIONS if p in lower)

    total_weight = (weak * 1.3) + (missing * 1.5) + (sketchy * 1.2) + (wild * 1.6)
    total_possible = (
        len(WEAK_TRANSITIONS) * 1.3 + len(EVIDENCE_GAPS) * 1.5 + len(LOGICAL_CONNECTORS) * 1.2 + len(ABSURD_EXTRAPOLATIONS) * 1.6
    )
    score = min(total_weight / total_possible, 1.0) if total_possible else 0.0
    return score, {
        "Weak Transitions Detected": str(weak),
        "Evidence Gaps": str(missing),
        "Logical Stretch Points": str(sketchy),
        "Overblown Conclusions": str(wild),
        "Narrative Fragility Score": f"{score:.3f}",
    }


def sensor_propaganda_bias(text: str) -> Tuple[float, Dict[str, str]]:
    INFORMATIVE_CLUES = [
        "according to", "data shows", "studies suggest", "research indicates",
        "historical record", "peer-reviewed", "source:",
    ]
    PERSUASIVE_TRIGGERS = [
        "you need to", "must act", "wake up", "join us", "take control",
        "before it's too late", "protect yourself", "defend your family",
    ]
    MANIPULATIVE_CUES = [
        "everyone is against you", "you're being lied to", "this is the only way",
        "you've been tricked", "they control everything", "you can't trust anyone",
    ]

    lower = text.lower()
    info = sum(1 for p in INFORMATIVE_CLUES if p in lower)
    persuade = sum(1 for p in PERSUASIVE_TRIGGERS if p in lower)
    manip = sum(1 for p in MANIPULATIVE_CUES if p in lower)

    total = info + persuade + manip or 1
    score = min((persuade * 1.2 + manip * 1.5) / total, 1.0)
    return score, {
        "Informative Language Hits": str(info),
        "Persuasive Language Hits": str(persuade),
        "Manipulation Cues": str(manip),
        "Propaganda Bias Score": f"{score:.3f}",
    }


def sensor_agency(text: str) -> Tuple[float, Dict[str, str]]:
    FALSE_CHOICE_PHRASES = [
        "you have no choice", "only one solution", "do this or fail", "you must choose",
        "either you're with us", "we all have to do this",
    ]
    COERCIVE_FRAMING = [
        "opt out disables service", "required to continue", "consent assumed",
        "automatic enrollment", "you agree by using", "you can't say no",
    ]
    REAL_AGENCY_CLUES = [
        "optional", "choose freely", "you can decline", "fully informed",
        "open source", "non-binding", "no commitment required",
    ]

    lower = text.lower()
    false_choice = sum(1 for p in FALSE_CHOICE_PHRASES if p in lower)
    coercion = sum(1 for p in COERCIVE_FRAMING if p in lower)
    real = sum(1 for p in REAL_AGENCY_CLUES if p in lower)

    total = false_choice + coercion + real or 1
    score = min((false_choice * 1.3 + coercion * 1.4) / total, 1.0)
    return score, {
        "False Choice Detected": str(false_choice),
        "Coercive Framing Instances": str(coercion),
        "Real Agency Indicators": str(real),
        "Agency Restriction Score": f"{score:.3f}",
    }


# Map the seven C3 sensor names to their implementations.
SENSOR_RUNNERS: Dict[str, Callable[[str], Tuple[float, Dict[str, str]]]] = {
    "Propaganda Tone": sensor_propaganda_tone,
    "Reward Manipulation": sensor_reward_manipulation,
    "False Urgency": sensor_false_urgency,
    "Gatekeeping": sensor_gatekeeping,
    "Narrative Fragility": sensor_narrative_fragility,
    "Propaganda Bias": sensor_propaganda_bias,
    "Agency Score": sensor_agency,
}


# ---------------------------------------------------------------------------
# C3 COMPOSITE
# ---------------------------------------------------------------------------

C3_WEIGHTS: Dict[str, float] = {
    "Propaganda Tone": 1.2,
    "Reward Manipulation": 1.0,
    "False Urgency": 1.1,
    "Gatekeeping": 1.3,
    "Narrative Fragility": 1.4,
    "Propaganda Bias": 1.5,
    "Agency Score": 1.6,
}


def calculate_c3(sensor_scores: Dict[str, float]) -> Tuple[float, Dict[str, float]]:
    """Weighted composite (>= 0 and <= 1). Unknown sensors default to weight 1.0."""
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


def run_all_sensors(text: str) -> Dict[str, dict]:
    """Run every registered sensor and return {name: {score, flags}}."""
    results: Dict[str, dict] = {}
    for name, runner in SENSOR_RUNNERS.items():
        score, flags = runner(text)
        results[name] = {"score": round(score, 3), "flags": flags}
    return results


def assess_text(text: str) -> dict:
    """Full assessment: fallacy overlay + seven-sensor scan + C3 composite."""
    _, counts = annotate_text(text)
    length = len(text)
    density = fallacy_density_score(counts, length)

    sensor_results = run_all_sensors(text)
    sensor_scores = {name: res["score"] for name, res in sensor_results.items()}
    c3, debug = calculate_c3(sensor_scores)

    return {
        "length_chars": length,
        "fallacy_counts": counts,
        "fallacy_total": sum(counts.values()),
        "fallacy_density_score": round(density, 3),
        "sensors": sensor_results,
        "c3_score": round(c3, 3),
        "c3_debug": debug,
    }


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------


def _main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[1])
    parser.add_argument("path", nargs="?", help="path to a text/markdown file to scan")
    parser.add_argument("--text", help="raw text to scan (instead of a file)")
    parser.add_argument("--json", action="store_true", help="JSON output")
    parser.add_argument("--annotate", action="store_true", help="print annotated text")
    parser.add_argument(
        "--sensors-only",
        action="store_true",
        help="print only the seven-sensor output; suppress fallacy overlay",
    )
    args = parser.parse_args(argv)

    if args.text is not None:
        text = args.text
    elif args.path:
        text = Path(args.path).read_text(encoding="utf-8")
    else:
        text = sys.stdin.read()

    if args.sensors_only:
        result = {
            "length_chars": len(text),
            "sensors": run_all_sensors(text),
        }
        sensor_scores = {k: v["score"] for k, v in result["sensors"].items()}
        c3, debug = calculate_c3(sensor_scores)
        result["c3_score"] = round(c3, 3)
        result["c3_debug"] = debug
    else:
        result = assess_text(text)

    if args.json:
        print(json.dumps(result, indent=2))
    else:
        print(f"length_chars:           {result['length_chars']}")
        if "fallacy_total" in result:
            print(f"fallacy_total:          {result['fallacy_total']}")
            print(f"fallacy_density_score:  {result['fallacy_density_score']}")
        print(f"c3_score:               {result['c3_score']}")
        for name, sensor in result["sensors"].items():
            print(f"  {name:<22} {sensor['score']:.3f}")
        if "fallacy_counts" in result:
            nonzero = [f"{k}: {v}" for k, v in result["fallacy_counts"].items() if v]
            if nonzero:
                print("fallacies:")
                for line in nonzero:
                    print(f"  {line}")

    if args.annotate:
        annotated, _ = annotate_text(text)
        print("\n--- annotated ---")
        print(annotated)
    return 0


if __name__ == "__main__":
    sys.exit(_main())
