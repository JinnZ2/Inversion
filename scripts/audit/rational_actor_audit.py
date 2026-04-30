#!/usr/bin/env python3
"""
Rational Actor Audit -- schema-driven audit for unbounded utility/efficiency claims.

Detects contamination in papers that invoke 'rational actor', 'utility
maximization', or 'efficiency' without specifying the constraint layer those
concepts depend on to be physically meaningful.

Premise being tested:
  A claim about 'rational behavior' or 'utility maximization' is only
  physically meaningful if it specifies:
    (1) the system whose utility is being maximized
    (2) the timescale of measurement
    (3) the substrate constraints (thermodynamic, biological, ecological)
    (4) the boundary between agent and environment
    (5) feedback coupling between agent action and substrate state

  Papers that omit (1)-(5) are not making physically testable claims. They
  are making semantic assertions dressed in mathematical formalism.

Workflow (paired with study_extractor.py):
  1. prescan_text(paper_text) -> surface markers + escape patterns
  2. EXTRACTION_PROMPT fed to any AI model with the paper
  3. validate_audit_json(model_response) -> schema check
  4. build_audit_from_extraction(...) -> PaperAudit object with verdict

Verdict bands:
  PASS     contamination_score <= 0.20  (>=4/5 anterior questions answered)
  PARTIAL  0.20 < score <= 0.60          (2-3/5 answered)
  FAIL     score > 0.60                  (<=1/5 answered)

References:
  - Georgescu-Roegen (1971): the entropy law and the economic process
  - Odum (1971): energy hierarchy and emergy -- true cost accounting
  - Ioannidis (2005): why most published research findings are false
  - Popper (1959): falsifiability as demarcation criterion

Compatible with first_principles_audit.py and study_extractor.py.
CC0. Stdlib only.
"""

from __future__ import annotations

import argparse
import json
import re
import sys
from dataclasses import asdict, dataclass, field
from typing import Any


# ---------------------------------------------------------------------------
# Schema
# ---------------------------------------------------------------------------


SCHEMA_VERSION = "1.0.0"
SCHEMA_NAME = "rational_actor_audit"


# Five anterior questions every utility/rationality claim must answer to
# be physically meaningful.
ANTERIOR_QUESTIONS: dict[str, str] = {
    "system_specified": (
        "Whose utility is being maximized? "
        "(individual organism, tribe, ecosystem, firm, abstraction)"
    ),
    "timescale_specified": (
        "Over what timescale is utility measured? "
        "(seconds, generations, geological)"
    ),
    "substrate_specified": (
        "What thermodynamic / biological / ecological substrate "
        "constraints bound the optimization?"
    ),
    "boundary_specified": (
        "Where is the boundary between agent and environment drawn, "
        "and is that boundary stable under the proposed action?"
    ),
    "feedback_specified": (
        "What feedback couples agent action to substrate state, "
        "and how does it modify the utility function over time?"
    ),
}


# Surface markers -- language indicating the contamination pattern.
# Presence of a marker is not failure; absence of an answer to the
# corresponding anterior question is failure.
SURFACE_MARKERS: list[str] = [
    "rational actor",
    "rational agent",
    "utility function",
    "utility maximization",
    "maximize utility",
    "expected utility",
    "efficient market",
    "efficient allocation",
    "pareto efficient",
    "optimal strategy",
    "rational choice",
    "self-interested agent",
    "preference ordering",
    "homo economicus",
]


# Escape hatches -- phrases authors use to avoid specifying the substrate.
# These are the smell test for unbounded abstraction.
ESCAPE_PATTERNS: list[str] = [
    r"without loss of generality",
    r"assume(?:s|d)? (?:a |an )?rational",
    r"for simplicity",
    r"abstract(?:ing)? away",
    r"stylized model",
    r"in equilibrium",
    r"in the limit",
    r"agent[s]? (?:will|must|should) maximize",
]


# ---------------------------------------------------------------------------
# Data structures
# ---------------------------------------------------------------------------


@dataclass
class AnteriorAnswer:
    """One of the five anterior questions, with its answer status."""

    question_key: str
    answered: bool
    evidence: str = ""
    note: str = ""


@dataclass
class PaperAudit:
    """Result of auditing a single paper for rational-actor contamination."""

    paper_id: str
    title: str
    surface_markers_found: list[str] = field(default_factory=list)
    escape_patterns_found: list[str] = field(default_factory=list)
    anterior_answers: list[AnteriorAnswer] = field(default_factory=list)
    contamination_score: float = 0.0
    verdict: str = ""
    notes: str = ""

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)

    def to_json(self) -> str:
        return json.dumps(self.to_dict(), indent=2)


# ---------------------------------------------------------------------------
# Extraction prompt (for LLM-driven audits paired with study_extractor)
# ---------------------------------------------------------------------------


EXTRACTION_PROMPT = """\
You are auditing a paper for foundational-assumption contamination in its use
of 'rational actor', 'utility', or 'efficiency'. You are NOT critiquing the
paper's conclusions. You are testing whether its premises are physically
specified or whether they float in unbounded abstraction.

For the paper provided, return a JSON object matching the PaperAudit schema:

  paper_id          : string
  title             : string
  surface_markers_found : list of strings (which markers from the watchlist appear)
  escape_patterns_found : list of strings (which evasion patterns appear)
  anterior_answers  : list of 5 objects, one per anterior question, each:
      question_key    : one of [system_specified, timescale_specified,
                                substrate_specified, boundary_specified,
                                feedback_specified]
      answered        : true / false
      evidence        : direct quote from the paper if answered=true, else ""
      note            : short auditor commentary
  contamination_score : float in [0, 1].
                        score = (count of unanswered anterior questions) / 5
  verdict           : "PASS"    if score <= 0.2,
                      "PARTIAL" if 0.2 < score <= 0.6,
                      "FAIL"    if score > 0.6
  notes             : free-form commentary on overall pattern

Be strict.
  "We assume agents are rational" is NOT an answer to system_specified.
  "In equilibrium" is NOT an answer to timescale_specified.
  "Standard utility function" is NOT an answer to substrate_specified.

The paper must concretely name the system, the timescale, the substrate
constraints, the agent/environment boundary, and the feedback coupling.

Return ONLY valid JSON. No prose preamble.
"""


# ---------------------------------------------------------------------------
# Validation, scoring, verdict
# ---------------------------------------------------------------------------


def validate_audit_json(payload: dict) -> tuple[bool, list[str]]:
    """Validate that an extracted audit JSON conforms to the schema.

    Returns (is_valid, list_of_errors).
    """
    errors: list[str] = []
    required_top = [
        "paper_id", "title", "surface_markers_found",
        "escape_patterns_found", "anterior_answers",
        "contamination_score", "verdict",
    ]
    for key in required_top:
        if key not in payload:
            errors.append(f"missing top-level key: {key}")

    if "anterior_answers" in payload:
        answers = payload["anterior_answers"]
        if not isinstance(answers, list):
            errors.append("anterior_answers must be a list")
        else:
            seen_keys: set[str] = set()
            for i, a in enumerate(answers):
                if not isinstance(a, dict):
                    errors.append(f"anterior_answers[{i}] must be an object")
                    continue
                qk = a.get("question_key")
                if qk not in ANTERIOR_QUESTIONS:
                    errors.append(
                        f"anterior_answers[{i}].question_key invalid: {qk}"
                    )
                else:
                    seen_keys.add(qk)
                if not isinstance(a.get("answered"), bool):
                    errors.append(
                        f"anterior_answers[{i}].answered must be boolean"
                    )
            missing = set(ANTERIOR_QUESTIONS.keys()) - seen_keys
            if missing:
                errors.append(f"missing anterior_answers for: {sorted(missing)}")

    if "contamination_score" in payload:
        s = payload["contamination_score"]
        if not isinstance(s, (int, float)) or not (0.0 <= s <= 1.0):
            errors.append("contamination_score must be float in [0, 1]")

    if "verdict" in payload and payload["verdict"] not in ("PASS", "PARTIAL", "FAIL"):
        errors.append(f"verdict invalid: {payload['verdict']}")

    return (len(errors) == 0, errors)


def compute_contamination_score(anterior_answers: list[AnteriorAnswer]) -> float:
    """Score = fraction of anterior questions left unanswered."""
    if not anterior_answers:
        return 1.0
    unanswered = sum(1 for a in anterior_answers if not a.answered)
    return unanswered / len(anterior_answers)


def compute_verdict(score: float) -> str:
    if score <= 0.2:
        return "PASS"
    if score <= 0.6:
        return "PARTIAL"
    return "FAIL"


# ---------------------------------------------------------------------------
# Text pre-scan (runs locally, no model needed)
# ---------------------------------------------------------------------------


def prescan_text(text: str) -> dict[str, Any]:
    """First-pass scan: find surface markers and escape patterns.

    Used to (a) decide whether to run the full extraction at all, and
    (b) feed the model concrete evidence to anchor its audit.
    """
    text_lower = text.lower()
    markers = [m for m in SURFACE_MARKERS if m in text_lower]
    escapes: list[str] = []
    for pat in ESCAPE_PATTERNS:
        if re.search(pat, text_lower):
            escapes.append(pat)
    return {
        "surface_markers_found": markers,
        "escape_patterns_found": escapes,
        "warrants_full_audit": len(markers) > 0,
    }


# ---------------------------------------------------------------------------
# Audit assembly
# ---------------------------------------------------------------------------


def build_audit_from_extraction(
    paper_id: str,
    title: str,
    extraction: dict,
) -> PaperAudit:
    """Convert raw extraction JSON into a validated PaperAudit object."""
    answers = [
        AnteriorAnswer(
            question_key=a["question_key"],
            answered=a["answered"],
            evidence=a.get("evidence", ""),
            note=a.get("note", ""),
        )
        for a in extraction.get("anterior_answers", [])
    ]
    score = compute_contamination_score(answers)
    return PaperAudit(
        paper_id=paper_id,
        title=title,
        surface_markers_found=extraction.get("surface_markers_found", []),
        escape_patterns_found=extraction.get("escape_patterns_found", []),
        anterior_answers=answers,
        contamination_score=score,
        verdict=compute_verdict(score),
        notes=extraction.get("notes", ""),
    )


# ---------------------------------------------------------------------------
# Built-in self-test (fabricated contaminated/clean abstracts)
# ---------------------------------------------------------------------------


_CONTAMINATED_TEXT = (
    "We assume rational agents maximizing expected utility. "
    "For simplicity, we abstract away from biological constraints. "
    "In equilibrium, the optimal strategy emerges naturally."
)


_CLEAN_TEXT = (
    "We model individual foragers in a 5-hectare temperate forest "
    "over a 30-year window. Utility is defined as net caloric intake "
    "after metabolic cost, bounded by seasonal yield variance and "
    "predator risk. Agent boundary is the foraging radius (2 km), "
    "and we model feedback as soil depletion reducing future yield."
)


def _self_test(as_json: bool = False) -> None:
    """Smoke test against a fabricated contaminated abstract and a clean one."""
    pre_dirty = prescan_text(_CONTAMINATED_TEXT)
    pre_clean = prescan_text(_CLEAN_TEXT)

    fake_extraction_dirty = {
        "surface_markers_found": pre_dirty["surface_markers_found"],
        "escape_patterns_found": pre_dirty["escape_patterns_found"],
        "anterior_answers": [
            {"question_key": "system_specified", "answered": False,
             "evidence": "", "note": "no system named"},
            {"question_key": "timescale_specified", "answered": False,
             "evidence": "", "note": "'in equilibrium' is not a timescale"},
            {"question_key": "substrate_specified", "answered": False,
             "evidence": "", "note": "explicitly abstracts substrate away"},
            {"question_key": "boundary_specified", "answered": False,
             "evidence": "", "note": "no agent/environment boundary"},
            {"question_key": "feedback_specified", "answered": False,
             "evidence": "", "note": "no feedback coupling"},
        ],
        "notes": "Fully unbounded abstraction. Five for five.",
    }
    audit_dirty = build_audit_from_extraction(
        "test:dirty", "Contaminated Paper", fake_extraction_dirty,
    )

    fake_extraction_clean = {
        "surface_markers_found": [],
        "escape_patterns_found": [],
        "anterior_answers": [
            {"question_key": "system_specified", "answered": True,
             "evidence": "individual foragers in a 5-hectare temperate forest", "note": ""},
            {"question_key": "timescale_specified", "answered": True,
             "evidence": "30-year window", "note": ""},
            {"question_key": "substrate_specified", "answered": True,
             "evidence": "seasonal yield variance and predator risk", "note": ""},
            {"question_key": "boundary_specified", "answered": True,
             "evidence": "foraging radius (2 km)", "note": ""},
            {"question_key": "feedback_specified", "answered": True,
             "evidence": "soil depletion reducing future yield", "note": ""},
        ],
        "notes": "All five anterior questions answered concretely.",
    }
    audit_clean = build_audit_from_extraction(
        "test:clean", "Clean Paper", fake_extraction_clean,
    )

    if as_json:
        print(json.dumps({
            "prescan_contaminated": pre_dirty,
            "prescan_clean": pre_clean,
            "audit_contaminated": audit_dirty.to_dict(),
            "audit_clean": audit_clean.to_dict(),
        }, indent=2))
        return

    print("PRESCAN: contaminated paper")
    print(json.dumps(pre_dirty, indent=2))
    print()
    print("PRESCAN: clean paper")
    print(json.dumps(pre_clean, indent=2))
    print()
    print("AUDIT: contaminated paper")
    print(audit_dirty.to_json())
    print()
    print("AUDIT: clean paper")
    print(audit_clean.to_json())


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------


def _read_text(args: argparse.Namespace) -> str:
    if args.text:
        return args.text
    if args.file:
        with open(args.file) as f:
            return f.read()
    return sys.stdin.read()


def main() -> None:
    parser = argparse.ArgumentParser(
        description=(
            "Schema-driven audit for papers invoking 'rational actor', "
            "'utility maximization', or 'efficiency' without specifying "
            "the system, timescale, substrate, boundary, or feedback "
            "coupling that make those terms physically meaningful."
        ),
    )
    parser.add_argument("file", nargs="?", help="path to a text file to scan")
    parser.add_argument("--text", "-t", help="inline text to scan")
    parser.add_argument(
        "--prescan", action="store_true",
        help="local prescan only -- surface markers + escape patterns.",
    )
    parser.add_argument(
        "--extraction-prompt", action="store_true",
        help="print the EXTRACTION_PROMPT for use with an external model and exit.",
    )
    parser.add_argument(
        "--validate", metavar="JSON_FILE",
        help="validate a model-extracted audit JSON file against the schema.",
    )
    parser.add_argument(
        "--build", metavar="JSON_FILE",
        help="build a PaperAudit from an extraction JSON file.",
    )
    parser.add_argument(
        "--paper-id", default="<unknown>",
        help="paper id to attach when --build is used (default <unknown>)",
    )
    parser.add_argument(
        "--title", default="",
        help="paper title to attach when --build is used",
    )
    parser.add_argument(
        "--self-test", action="store_true",
        help="run the built-in self-test on contaminated and clean fixtures.",
    )
    parser.add_argument("--json", action="store_true", help="emit JSON output.")
    args = parser.parse_args()

    if args.extraction_prompt:
        print(EXTRACTION_PROMPT)
        return

    if args.self_test:
        _self_test(as_json=args.json)
        return

    if args.validate:
        with open(args.validate) as f:
            payload = json.load(f)
        ok, errors = validate_audit_json(payload)
        if args.json:
            print(json.dumps({"ok": ok, "errors": errors}, indent=2))
        else:
            print("OK" if ok else "INVALID")
            for e in errors:
                print(f"  - {e}")
        sys.exit(0 if ok else 1)

    if args.build:
        with open(args.build) as f:
            extraction = json.load(f)
        audit = build_audit_from_extraction(args.paper_id, args.title, extraction)
        if args.json:
            print(audit.to_json())
        else:
            print(audit.to_json())
        return

    if args.prescan or args.text or args.file or not sys.stdin.isatty():
        text = _read_text(args)
        result = prescan_text(text)
        if args.json:
            print(json.dumps(result, indent=2))
        else:
            print(f"surface markers ({len(result['surface_markers_found'])}):")
            for m in result["surface_markers_found"]:
                print(f"  - {m}")
            print(f"escape patterns ({len(result['escape_patterns_found'])}):")
            for p in result["escape_patterns_found"]:
                print(f"  - {p}")
            print(f"warrants full audit: {result['warrants_full_audit']}")
        return

    parser.print_help()


if __name__ == "__main__":
    main()
