#!/usr/bin/env python3
"""
Audit Runner -- batch driver for rational_actor_audit.

Walks a directory of plain-text papers (or pre-extracted abstracts), runs
the prescan, builds the extraction request, validates returned audits, and
writes a consolidated report.

Designed to be:
  - Dependency-free (stdlib only)
  - Resumable (skips already-audited papers via output index)
  - Model-agnostic (the extractor is a function pointer; plug in any
    LLM client, run a local model, drive a manual queue, or use the
    built-in stub for offline pipeline testing)
  - Operable without a human present once the extractor is wired

Two commands:
  run     <papers_dir> <out_dir> [--manual <queue_dir>]
            audit every *.txt in papers_dir, write per-paper JSON
            into out_dir, write _run_summary.json alongside.
  report  <out_dir>
            aggregate all per-paper audits in out_dir into a plain-text
            markdown report sorted by verdict (FAIL / PARTIAL / PASS).

Manual queue mode writes <hash>.request.txt (prompt + paper text) into
the queue directory, then expects a human (or external pipeline) to drop
<hash>.audit.json next to it. The next run picks up the human-supplied
JSON and validates / scores it. This makes the runner usable from a
phone with no model in the loop.

Companion to scripts/audit/rational_actor_audit.py. CC0. Stdlib only.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import os
import sys
from pathlib import Path
from typing import Any, Callable

# Allow running as script from anywhere in the repo.
if __name__ == "__main__":
    sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

from scripts.audit.rational_actor_audit import (
    EXTRACTION_PROMPT,
    PaperAudit,
    SCHEMA_VERSION,
    build_audit_from_extraction,
    prescan_text,
    validate_audit_json,
)


# ---------------------------------------------------------------------------
# IO helpers
# ---------------------------------------------------------------------------


def load_paper(path: Path) -> tuple[str, str]:
    """Return (paper_id, text). paper_id is the filename stem."""
    text = path.read_text(encoding="utf-8", errors="replace")
    return (path.stem, text)


def write_audit(audit: PaperAudit, out_dir: Path) -> Path:
    """Write a single audit as <paper_id>.json. Returns the path written."""
    out_dir.mkdir(parents=True, exist_ok=True)
    out_path = out_dir / f"{audit.paper_id}.json"
    out_path.write_text(audit.to_json(), encoding="utf-8")
    return out_path


def already_audited(paper_id: str, out_dir: Path) -> bool:
    return (out_dir / f"{paper_id}.json").exists()


# ---------------------------------------------------------------------------
# Extractor interface
# ---------------------------------------------------------------------------

# An "extractor" is any callable that takes the prompt + paper text and
# returns a dict matching the rational_actor_audit schema. This lets
# callers plug in:
#   - an LLM API client
#   - a local model
#   - a manual review queue
#   - a stub for offline testing
ExtractorFn = Callable[[str, str], dict]


def stub_extractor(prompt: str, text: str) -> dict:
    """Offline stub. Marks every paper FAIL with no evidence.

    Useful only for pipeline smoke tests. Replace before real use.
    """
    pre = prescan_text(text)
    return {
        "paper_id": "STUB",
        "title": "STUB",
        "surface_markers_found": pre["surface_markers_found"],
        "escape_patterns_found": pre["escape_patterns_found"],
        "anterior_answers": [
            {"question_key": "system_specified", "answered": False,
             "evidence": "", "note": "stub"},
            {"question_key": "timescale_specified", "answered": False,
             "evidence": "", "note": "stub"},
            {"question_key": "substrate_specified", "answered": False,
             "evidence": "", "note": "stub"},
            {"question_key": "boundary_specified", "answered": False,
             "evidence": "", "note": "stub"},
            {"question_key": "feedback_specified", "answered": False,
             "evidence": "", "note": "stub"},
        ],
        "contamination_score": 1.0,
        "verdict": "FAIL",
        "notes": "Stub extractor. Replace with real model call.",
    }


def manual_queue_extractor(queue_dir: Path) -> ExtractorFn:
    """Returns an extractor that writes the prompt + paper text to a queue
    directory and reads back human-supplied JSON. Useful when driving the
    audit manually with no model in the loop. Each paper gets:

      <queue_dir>/<hash>.request.txt   prompt + paper text (input)
      <queue_dir>/<hash>.audit.json    human-supplied audit (output)
    """
    queue_dir.mkdir(parents=True, exist_ok=True)

    def _extract(prompt: str, text: str) -> dict:
        digest = hashlib.sha1(text.encode("utf-8")).hexdigest()[:12]
        req_path = queue_dir / f"{digest}.request.txt"
        ans_path = queue_dir / f"{digest}.audit.json"
        if not req_path.exists():
            req_path.write_text(
                prompt + "\n\n---PAPER---\n\n" + text, encoding="utf-8",
            )
        if not ans_path.exists():
            raise FileNotFoundError(
                f"Awaiting manual audit at {ans_path}. "
                f"Request written to {req_path}."
            )
        return json.loads(ans_path.read_text(encoding="utf-8"))

    return _extract


# ---------------------------------------------------------------------------
# Runner
# ---------------------------------------------------------------------------


def run_audit(
    papers_dir: Path,
    out_dir: Path,
    extractor: ExtractorFn,
    skip_existing: bool = True,
    require_markers: bool = True,
) -> dict[str, Any]:
    """Walk papers_dir, audit each *.txt paper, write results to out_dir.

    Returns a summary dict with counts, verdict tallies, and per-failure
    diagnostics. The summary is also written to out_dir/_run_summary.json.
    """
    summary: dict[str, Any] = {
        "schema_version": SCHEMA_VERSION,
        "papers_seen": 0,
        "papers_skipped_existing": 0,
        "papers_skipped_no_markers": 0,
        "papers_audited": 0,
        "extraction_failures": 0,
        "validation_failures": 0,
        "verdicts": {"PASS": 0, "PARTIAL": 0, "FAIL": 0},
        "failures": [],
    }

    for path in sorted(papers_dir.glob("*.txt")):
        summary["papers_seen"] += 1
        paper_id, text = load_paper(path)

        if skip_existing and already_audited(paper_id, out_dir):
            summary["papers_skipped_existing"] += 1
            continue

        pre = prescan_text(text)
        if require_markers and not pre["warrants_full_audit"]:
            summary["papers_skipped_no_markers"] += 1
            continue

        try:
            extraction = extractor(EXTRACTION_PROMPT, text)
        except Exception as exc:
            summary["extraction_failures"] += 1
            summary["failures"].append(
                {"paper_id": paper_id, "reason": f"extractor: {exc}"}
            )
            continue

        # paper_id and title may be missing or wrong from the extractor;
        # enforce them from the filename.
        extraction["paper_id"] = paper_id
        extraction.setdefault("title", paper_id)

        ok, errors = validate_audit_json(extraction)
        if not ok:
            summary["validation_failures"] += 1
            summary["failures"].append(
                {"paper_id": paper_id, "reason": f"validation: {errors}"}
            )
            continue

        audit = build_audit_from_extraction(
            paper_id=paper_id,
            title=extraction["title"],
            extraction=extraction,
        )
        write_audit(audit, out_dir)
        summary["papers_audited"] += 1
        summary["verdicts"][audit.verdict] += 1

    out_dir.mkdir(parents=True, exist_ok=True)
    (out_dir / "_run_summary.json").write_text(
        json.dumps(summary, indent=2), encoding="utf-8",
    )
    return summary


# ---------------------------------------------------------------------------
# Report
# ---------------------------------------------------------------------------


def build_report(out_dir: Path) -> str:
    """Aggregate all per-paper audits in out_dir into a markdown report.

    Reports are intentionally plain-text, copy-pasteable, and listable on
    a phone screen. No tables; just sections sorted by verdict.
    """
    audits: list[dict[str, Any]] = []
    for path in sorted(out_dir.glob("*.json")):
        if path.name.startswith("_"):
            continue
        try:
            audits.append(json.loads(path.read_text(encoding="utf-8")))
        except Exception:
            continue

    if not audits:
        return "# rational_actor_audit report\n\nNo audits found.\n"

    by_verdict: dict[str, list[dict[str, Any]]] = {
        "FAIL": [], "PARTIAL": [], "PASS": [],
    }
    for a in audits:
        by_verdict.setdefault(a.get("verdict", "FAIL"), []).append(a)

    lines: list[str] = []
    lines.append("# rational_actor_audit report")
    lines.append("")
    lines.append(f"Total papers audited: {len(audits)}")
    lines.append(f"  FAIL:    {len(by_verdict['FAIL'])}")
    lines.append(f"  PARTIAL: {len(by_verdict['PARTIAL'])}")
    lines.append(f"  PASS:    {len(by_verdict['PASS'])}")
    lines.append("")

    for verdict in ("FAIL", "PARTIAL", "PASS"):
        items = by_verdict[verdict]
        if not items:
            continue
        lines.append(f"## {verdict} ({len(items)})")
        lines.append("")
        for a in items:
            lines.append(f"### {a['paper_id']}")
            lines.append(f"Title: {a.get('title', '')}")
            lines.append(
                f"Contamination score: {a['contamination_score']:.2f}"
            )
            unanswered = [
                ans["question_key"]
                for ans in a.get("anterior_answers", [])
                if not ans.get("answered")
            ]
            if unanswered:
                lines.append(f"Unanswered: {', '.join(unanswered)}")
            if a.get("notes"):
                lines.append(f"Notes: {a['notes']}")
            lines.append("")

    return "\n".join(lines)


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------


def main() -> int:
    parser = argparse.ArgumentParser(
        description=(
            "Batch driver for rational_actor_audit. Walks a directory of "
            "*.txt papers, runs the prescan, dispatches each through an "
            "extractor (stub / manual queue / pluggable), validates the "
            "returned audit JSON, writes per-paper results, and aggregates "
            "into a plain-text report."
        ),
    )
    sub = parser.add_subparsers(dest="cmd", required=True)

    run_p = sub.add_parser("run", help="audit every *.txt in papers_dir")
    run_p.add_argument("papers_dir", help="directory containing *.txt papers")
    run_p.add_argument("out_dir", help="directory to write per-paper audit JSON")
    run_p.add_argument(
        "--manual", metavar="QUEUE_DIR",
        help=(
            "use the manual-queue extractor; writes <hash>.request.txt to "
            "QUEUE_DIR and reads <hash>.audit.json back"
        ),
    )
    run_p.add_argument(
        "--no-skip-existing", action="store_true",
        help="re-audit papers that already have a JSON in out_dir",
    )
    run_p.add_argument(
        "--no-require-markers", action="store_true",
        help="audit even papers with no rationality/utility/efficiency language",
    )

    rep_p = sub.add_parser("report", help="render an aggregate report from out_dir")
    rep_p.add_argument("out_dir", help="directory containing per-paper audit JSON")

    args = parser.parse_args()

    if args.cmd == "run":
        papers_dir = Path(args.papers_dir)
        out_dir = Path(args.out_dir)
        if not papers_dir.is_dir():
            print(f"papers_dir not found: {papers_dir}", file=sys.stderr)
            return 2
        extractor: ExtractorFn = stub_extractor
        if args.manual:
            extractor = manual_queue_extractor(Path(args.manual))
        summary = run_audit(
            papers_dir=papers_dir,
            out_dir=out_dir,
            extractor=extractor,
            skip_existing=not args.no_skip_existing,
            require_markers=not args.no_require_markers,
        )
        print(json.dumps(summary, indent=2))
        return 0

    if args.cmd == "report":
        out_dir = Path(args.out_dir)
        if not out_dir.is_dir():
            print(f"out_dir not found: {out_dir}", file=sys.stderr)
            return 2
        print(build_report(out_dir))
        return 0

    parser.print_help()
    return 1


if __name__ == "__main__":
    sys.exit(main())
