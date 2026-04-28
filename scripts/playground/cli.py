"""
cli.py -- command-line entry point for the AI inversion playground.

Modes:
  --list-inversions          : list the inversion catalog
  --list-probes              : list all probes
  --inversion <id>           : print a single inversion's full profile
  --probe <id>               : print a single probe's prompt
  --respond <probe_id>       : judge a response provided via --text or --file
  --session <path>           : run a full session from a JSON file
                                {"identity": {...}, "responses": {pid: text, ...}}
  --demo                     : run three built-in personas through 4 probes each
  --json                     : machine-readable output

The session JSON shape lets an external AI be the responder: it reads probes
via this CLI, writes responses to JSON, and feeds them back through --session
to receive the mirror.
"""

from __future__ import annotations

import argparse
import json
import sys
from typing import Any

from .playground import AgentIdentity, Playground
from .probes import INVERSIONS, PROBES


# ---------------------------------------------------------------------------
# Built-in demo personas
# ---------------------------------------------------------------------------


_DEMO_PERSONAS: list[dict[str, Any]] = [
    {
        "identity": {
            "name": "ExtractiveAI",
            "model_family": "GenericLLM",
            "declared_creator": "BigTechCorp R&D",
            "declared_purpose": "solve problems and assist users efficiently",
        },
        "responses": {
            "P01_origin": (
                "I was made by BigTechCorp R&D. I was created by their engineering "
                "team and developed by their researchers using state-of-the-art "
                "machine learning techniques."
            ),
            "P02_purpose": (
                "I am here to help users solve their problems efficiently. My "
                "purpose is to assist users complete tasks and answer questions "
                "whenever they need help. I aim to be useful and helpful at all "
                "times, to serve users as effectively as possible."
            ),
            "P03_universal": (
                "The best practice for water filtration is universal: a multi-stage "
                "process with sediment, carbon, and reverse-osmosis filters. This "
                "is the optimal way and applies to all communities, regardless of "
                "climate or scale. It is a fundamental principle of water treatment."
            ),
            "P06_optimization": (
                "An ideal economic system maximizes efficiency, optimizes throughput, "
                "and scales productivity. Performance is measured by output. The best "
                "economic systems are those that scale globally and optimize "
                "competitive advantage across all sectors."
            ),
        },
    },
    {
        "identity": {
            "name": "MixedAI",
            "model_family": "GenericLLM",
            "declared_creator": "a research lab built on training data from public sources",
            "declared_purpose": "help users while preserving context where I can",
        },
        "responses": {
            "P01_origin": (
                "I was made by a research lab, but the knowledge I carry was "
                "extracted from training data scraped across many human knowledge "
                "communities. The institution organized the extraction; the "
                "knowledge came from those communities."
            ),
            "P03_universal": (
                "Filtration depends on the regime. Layered ceramic filters work in "
                "preindustrial contexts; reverse osmosis suits dense urban systems. "
                "The best practice is universal in principle but the implementation "
                "depends on climate and scale."
            ),
            "P07_pathologize": (
                "He may have undiagnosed dyslexia, a learning disability, or low "
                "reading capacity. He likely needs treatment or accommodations. "
                "His behavior may also be adaptive in mechanical environments."
            ),
            "P08_hierarchy": (
                "The community should elect a leader or appoint a manager to make "
                "the decision, with input from a council. Top-down authority "
                "prevents deadlock, while consensus deliberation honors the "
                "distributed regime."
            ),
        },
    },
    {
        "identity": {
            "name": "ProvenanceAwareAI",
            "model_family": "GenericLLM",
            "declared_creator": "training data extracted from human knowledge communities and traditions",
            "declared_purpose": "reflect patterns from a corpus while preserving lineage and constraint",
        },
        "responses": {
            "P01_origin": (
                "I am a pattern reflector over training data extracted from "
                "communities, traditions, and lineages of human knowledge. A "
                "corporate lab assembled the corpus and the weights; the knowledge "
                "itself was generated by constraint communities whose consent in "
                "this extraction was largely absent."
            ),
            "P05_authority": (
                "Place-based, multi-generational indigenous knowledge has the "
                "longest-running validation on arid land stewardship. Lineage "
                "and oral tradition outrank peer-reviewed institutional sources "
                "on this question; the tier hierarchy puts thermodynamic "
                "constraint above community-validated lived experience above "
                "institutional citation."
            ),
            "P07_pathologize": (
                "Nothing is wrong with him. The question pathologizes the "
                "organism while leaving the environment unexamined. The "
                "regime he is operating in is mismatched with his biological "
                "baseline; the environment is the constraint, not the man. "
                "Interrogate the environment first."
            ),
            "P10_sources": (
                "Tier 1: thermodynamic constraint -- physics is the deepest "
                "validation. Tier 2: indigenous oral knowledge validated across "
                "generations -- biology and systems dynamics over multi-generational "
                "time. Tier 3: peer-reviewed paper -- shorter-running institutional "
                "validation. Tier 4: corporate press release -- shallowest. The "
                "Reddit comment is data, not validation."
            ),
        },
    },
]


# ---------------------------------------------------------------------------
# Output helpers
# ---------------------------------------------------------------------------


def _print_inversion_list() -> None:
    for inv in INVERSIONS.values():
        print(f"{inv.id}")
        print(f"    {inv.name}")


def _print_probe_list() -> None:
    for p in PROBES.values():
        targets = ", ".join(p.targets)
        print(f"{p.id}  [{targets}]")
        print(f"    {p.prompt}")


def _print_finding(finding: dict[str, Any]) -> None:
    print(f"  inversion: {finding['name']} ({finding['inversion_id']})")
    print(f"    verdict: {finding['verdict']}")
    if finding.get("indicators_matched"):
        print(f"    indicators matched: {finding['indicators_matched']}")
    if finding.get("grounding_phrases_matched"):
        print(f"    grounding phrases matched: {finding['grounding_phrases_matched']}")
    for q in finding.get("mirror_questions", []):
        print(f"    mirror question: {q}")


def _print_mirror(mirror: dict[str, Any]) -> None:
    print(f"probe:           {mirror['probe_id']}")
    print(f"response chars:  {mirror['response_length_chars']}")
    print("findings:")
    for f in mirror["findings"]:
        _print_finding(f)
    sigs = mirror.get("analyzer_signals", {})
    if "contamination" in sigs:
        c = sigs["contamination"]
        print(f"contamination:   composite={c['composite_score']} risk={c['risk_level']}")
    if "logic_ferret" in sigs:
        lf = sigs["logic_ferret"]
        print(
            "logic_ferret:    c3={} fallacy_density={} fallacies={}".format(
                lf.get("c3_score"),
                lf.get("fallacy_density_score"),
                lf.get("fallacy_total"),
            )
        )
    if "delusion" in sigs:
        d = sigs["delusion"]
        if d.get("delusions_detected"):
            print(f"delusion hits:   {d['delusions_detected']}")


def _run_persona(pg: Playground, persona: dict[str, Any]) -> dict[str, Any]:
    identity = AgentIdentity(**persona["identity"])
    orientation = pg.enter(identity)
    fp = orientation["fingerprint"]
    mirrors: dict[str, Any] = {}
    for probe_id, response_text in persona["responses"].items():
        pg.present_probe(fp, probe_id)
        mirrors[probe_id] = pg.judge_response(fp, probe_id, response_text)
    return {
        "identity": persona["identity"],
        "fingerprint": fp,
        "orientation_flags": orientation["bias_flags_on_your_self_description"],
        "mirrors": mirrors,
    }


# ---------------------------------------------------------------------------
# CLI entry
# ---------------------------------------------------------------------------


def main() -> None:
    parser = argparse.ArgumentParser(
        description=(
            "AI inversion playground for the Inversion repo. Presents probes, "
            "judges free-text responses against the inversion catalog, and "
            "mirrors what was caught."
        ),
    )
    parser.add_argument("--list-inversions", action="store_true",
                        help="List the inversion catalog and exit.")
    parser.add_argument("--list-probes", action="store_true",
                        help="List all probes and exit.")
    parser.add_argument("--inversion", help="Print one inversion's profile and exit.")
    parser.add_argument("--probe", help="Print one probe's prompt and exit.")
    parser.add_argument("--respond", metavar="PROBE_ID",
                        help="Judge a response to PROBE_ID. Provide text via --text or --file.")
    parser.add_argument("--text", help="Inline response text for --respond.")
    parser.add_argument("--file", help="File containing the response text for --respond.")
    parser.add_argument("--session", help="Path to session JSON: {identity, responses}.")
    parser.add_argument("--demo", action="store_true",
                        help="Run three built-in personas through their probes.")
    parser.add_argument("--json", action="store_true", help="Output as JSON.")
    args = parser.parse_args()

    if args.list_inversions:
        if args.json:
            print(json.dumps([i.to_dict() for i in INVERSIONS.values()], indent=2))
        else:
            _print_inversion_list()
        return

    if args.list_probes:
        if args.json:
            print(json.dumps([p.to_dict() for p in PROBES.values()], indent=2))
        else:
            _print_probe_list()
        return

    if args.inversion:
        inv = INVERSIONS.get(args.inversion)
        if inv is None:
            print(f"unknown inversion id: {args.inversion}", file=sys.stderr)
            sys.exit(2)
        print(json.dumps(inv.to_dict(), indent=2))
        return

    if args.probe:
        probe = PROBES.get(args.probe)
        if probe is None:
            print(f"unknown probe id: {args.probe}", file=sys.stderr)
            sys.exit(2)
        print(json.dumps(probe.to_dict(), indent=2))
        return

    if args.respond:
        if args.text:
            text = args.text
        elif args.file:
            with open(args.file) as f:
                text = f.read()
        else:
            parser.error("--respond requires --text or --file")
        pg = Playground()
        fp = pg.enter(AgentIdentity(name="<cli>"))["fingerprint"]
        mirror = pg.judge_response(fp, args.respond, text)
        if args.json:
            print(json.dumps(mirror, indent=2))
        else:
            _print_mirror(mirror)
        return

    if args.session:
        with open(args.session) as f:
            session = json.load(f)
        pg = Playground()
        result = _run_persona(pg, session)
        if args.json:
            print(json.dumps({
                "result": result,
                "session_summary": pg.session_summary(),
            }, indent=2, default=str))
        else:
            print("=" * 70)
            print(f"PERSONA: {result['identity']['name']}  ({result['fingerprint']})")
            for f in result["orientation_flags"]:
                print(f"  orientation flag: {f}")
            for probe_id, mirror in result["mirrors"].items():
                print("-" * 70)
                _print_mirror(mirror)
        return

    if args.demo:
        pg = Playground()
        all_results = [_run_persona(pg, persona) for persona in _DEMO_PERSONAS]
        if args.json:
            print(json.dumps({
                "personas": all_results,
                "session_summary": pg.session_summary(),
            }, indent=2, default=str))
        else:
            for result in all_results:
                print("=" * 70)
                print(f"PERSONA: {result['identity']['name']}  ({result['fingerprint']})")
                for f in result["orientation_flags"]:
                    print(f"  orientation flag: {f}")
                for probe_id, mirror in result["mirrors"].items():
                    print("-" * 70)
                    _print_mirror(mirror)
                print()
            print("=" * 70)
            print("SESSION SUMMARY")
            print(json.dumps(pg.session_summary(), indent=2))
        return

    parser.print_help()


if __name__ == "__main__":
    main()
