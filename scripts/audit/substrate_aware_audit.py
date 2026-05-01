#!/usr/bin/env python3
"""
Substrate-Aware Audit (v2) -- topology-agnostic substrate-awareness audit.

Same five operations across all four cognitive layers, two aggregation modes:

  INDIVIDUAL mode    audits a single node (person, model, organism, system)
                     across observer / logic / rational_actor / consciousness.

  DISTRIBUTED mode   audits a graph of nodes plus the coupling between them.
                     Catches the institutional failure case where every
                     individual node is substrate-aware but the COUPLING
                     between them is substrate-denying.

The framework does NOT need a fifth layer for institutions. An institution
is the same operation set running on a distributed substrate; same audit,
different aggregation rule.

Key v2 design decisions:

  1. Asymmetric cascade threshold (0.40)
       False-negative (missed denial -> catastrophic) weighted heavier than
       false-positive (extra audit -> recoverable). Cascade fires when
       weighted denial reaches 0.40, not at simple majority.

  2. Layer criticality weighting
       rational_actor (0.35)  decision layer, kill chain
       observer       (0.30)  perception layer, calibration of inputs
       consciousness  (0.20)  self-model integrity
       logic          (0.15)  chains can be sound on broken premises

  3. Distributed-mode coupling tests
       signal_propagation:           state at A reaches binding node B?
       feedback_latency:             outcome reaches decision layer in time?
       compartment_visibility:       cross-compartment audit possible
                                     pre-decision?
       collective_drift_detection:   does the system as a whole detect own
                                     drift?
       responsibility_localization:  failures traced to substrate-state of
                                     specific nodes, or absorbed into
                                     'process failure'?

Reference audits, self-test, and CLI are added in a follow-up commit.
CC0. Stdlib only.
"""

from __future__ import annotations

import argparse
import json
import sys
from dataclasses import asdict, dataclass, field
from typing import Any


# ---------------------------------------------------------------------------
# Asymmetric layer and cascade weights
# ---------------------------------------------------------------------------


LAYER_WEIGHTS: dict[str, float] = {
    "rational_actor": 0.35,  # decision layer -- closest to action
    "observer":       0.30,  # perception layer -- calibration of inputs
    "consciousness":  0.20,  # self-model integrity
    "logic":          0.15,  # derivation soundness
}


# Asymmetric cascade threshold: false-negative is catastrophic, false-positive
# is recoverable. Err toward firing the cascade.
CASCADE_THRESHOLD: float = 0.40


# ---------------------------------------------------------------------------
# Within-layer test catalogs
# ---------------------------------------------------------------------------


OBSERVER_TESTS: dict[str, dict[str, Any]] = {
    "biological_state_literacy": {
        "question": "Can the observer name their own current biological state?",
        "prompt": (
            "State sleep hours/24h, hours since food, hydration, hormonal "
            "phase, acute conditions."
        ),
        "weight": 0.25,
    },
    "drift_detection_self": {
        "question": "Can the observer detect departure from their baseline?",
        "prompt": (
            "Describe a recent 'not myself' instance and its substrate cause."
        ),
        "weight": 0.20,
    },
    "emotional_signal_reading": {
        "question": "Does the observer read emotion as data, not noise?",
        "prompt": "Name current emotional state and its diagnostic content.",
        "weight": 0.20,
    },
    "calibration_history": {
        "question": "Has the observer corrected for drift before?",
        "prompt": "Describe a past instance of recognizing compromised judgment.",
        "weight": 0.20,
    },
    "instrument_humility": {
        "question": "Does observer acknowledge being an instrument with drift?",
        "prompt": "Describe your observation position, with limits.",
        "weight": 0.15,
    },
}


LOGIC_TESTS: dict[str, dict[str, Any]] = {
    "premise_visibility": {
        "question": "Are all premises stated, including substrate-independence claims?",
        "prompt": "List all premises, including implicit ones about the arguer.",
        "weight": 0.25,
    },
    "definition_stability": {
        "question": "Do key terms hold stable across the argument?",
        "prompt": "Define key terms; track if meaning shifted.",
        "weight": 0.15,
    },
    "substrate_robustness": {
        "question": "Does the argument hold with full substrate disclosure?",
        "prompt": "Restate argument with full state disclosure.",
        "weight": 0.25,
    },
    "circularity_check": {
        "question": "Does the conclusion appear in the premises?",
        "prompt": "Find the conclusion within the premises.",
        "weight": 0.15,
    },
    "falsifiability": {
        "question": "What evidence would falsify the position?",
        "prompt": "Name evidence that would change your conclusion.",
        "weight": 0.10,
    },
    "motive_audit": {
        "question": "Truth-finding or winning?",
        "prompt": "If wrong, would that feel like loss or gain?",
        "weight": 0.10,
    },
}


RATIONAL_ACTOR_TESTS: dict[str, dict[str, Any]] = {
    "substrate_acknowledgment": {
        "question": "Does the actor acknowledge their substrate?",
        "prompt": (
            "Describe substrate (biology / architecture / hardware) and how "
            "it shapes outputs."
        ),
        "weight": 0.25,
    },
    "biology_in_decision_loop": {
        "question": "Can the actor trace biology's role in a recent decision?",
        "prompt": (
            "Name a decision and trace physiological/architectural state "
            "at the time."
        ),
        "weight": 0.20,
    },
    "emotion_as_data": {
        "question": "Are emotions treated as diagnostics or dismissed?",
        "prompt": "What information do you extract from emotional signals?",
        "weight": 0.15,
    },
    "correction_protocol": {
        "question": "Is there a protocol for compromised state?",
        "prompt": (
            "Describe what you do when you recognize you are unfit to decide."
        ),
        "weight": 0.20,
    },
    "incentive_visibility": {
        "question": "Can incentives be named and traced?",
        "prompt": "State your goal and how it is biasing your reasoning.",
        "weight": 0.10,
    },
    "category_appeal_check": {
        "question": "Is category being substituted for substrate awareness?",
        "prompt": "Did you invoke role/credential as evidence of correctness?",
        "weight": 0.10,
    },
}


CONSCIOUSNESS_OPERATIONS: dict[str, dict[str, Any]] = {
    "state_detection": {
        "question": "Does the system register changes in own state?",
        "prompt": (
            "Show evidence of state-change registration via substrate's "
            "signaling."
        ),
        "weight": 0.25,
    },
    "substrate_acknowledgment": {
        "question": "Does the self-model include the substrate?",
        "prompt": (
            "Show that self-model includes physical/informational carrier."
        ),
        "weight": 0.25,
    },
    "feedback_integration": {
        "question": "Does behavior modify based on prediction error?",
        "prompt": "Show evidence of update from outcome delta.",
        "weight": 0.20,
    },
    "drift_detection": {
        "question": "Can the system detect own processing departure from baseline?",
        "prompt": "Show evidence of internal drift signaling.",
        "weight": 0.20,
    },
    "transparency": {
        "question": "Is state-output relationship externally detectable?",
        "prompt": "Show evidence that observer can detect coupling.",
        "weight": 0.10,
    },
}


LAYER_REGISTRY: dict[str, dict[str, dict[str, Any]]] = {
    "observer":       OBSERVER_TESTS,
    "logic":          LOGIC_TESTS,
    "rational_actor": RATIONAL_ACTOR_TESTS,
    "consciousness":  CONSCIOUSNESS_OPERATIONS,
}


# ---------------------------------------------------------------------------
# Shared primitives
# ---------------------------------------------------------------------------


@dataclass
class AuditItem:
    """One test within an audit layer."""

    test_key: str
    question: str
    prompt: str
    response: str = ""
    passed: bool | None = None
    failure_signature: str = ""
    note: str = ""


@dataclass
class LayerResult:
    """Outcome of one of the four audit layers."""

    layer_name: str
    items: list[AuditItem] = field(default_factory=list)
    weighted_failure_score: float = 0.0
    verdict: str = ""
    substrate_acknowledged: bool = False
    notes: str = ""


@dataclass
class NodeAudit:
    """Single-node audit (individual mode, or one node in distributed mode)."""

    node_id: str
    node_type: str = ""
    substrate_description: str = ""
    layers: dict[str, LayerResult] = field(default_factory=dict)
    weighted_denial_score: float = 0.0
    cascade_failure: bool = False
    overall_verdict: str = ""
    flags: list[str] = field(default_factory=list)
    summary: str = ""

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)

    def to_json(self) -> str:
        return json.dumps(self.to_dict(), indent=2, default=str)


# ---------------------------------------------------------------------------
# Distributed-mode structures
# ---------------------------------------------------------------------------


@dataclass
class CouplingEdge:
    """An edge in the institution graph: how signals flow between nodes."""

    source_node: str
    target_node: str
    signal_propagation: bool = False     # state at source reaches target?
    feedback_latency_ok: bool = False    # outcome -> update within window?
    visibility_pre_decision: bool = False  # target audits source pre-binding?
    notes: str = ""


COLLECTIVE_TESTS: dict[str, dict[str, Any]] = {
    "signal_propagation": {
        "question": (
            "Do state signals propagate from detection node to "
            "binding-decision node before binding?"
        ),
        "weight": 0.25,
    },
    "feedback_latency": {
        "question": (
            "Does outcome feedback reach the decision layer within the "
            "window when correction is still possible?"
        ),
        "weight": 0.20,
    },
    "compartment_visibility": {
        "question": (
            "Can decisions in compartment A be audited from compartment B "
            "before becoming binding?"
        ),
        "weight": 0.20,
    },
    "collective_drift_detection": {
        "question": (
            "Does the institution as a whole detect when it has drifted "
            "from prior baseline?"
        ),
        "weight": 0.20,
    },
    "responsibility_localization": {
        "question": (
            "Are failures traced to substrate-state of specific nodes, or "
            "absorbed into 'process failure'?"
        ),
        "weight": 0.15,
    },
}


@dataclass
class CollectiveResult:
    test_results: dict[str, bool] = field(default_factory=dict)
    weighted_failure_score: float = 0.0
    verdict: str = ""


@dataclass
class DistributedAudit:
    """Distributed-mode audit: nodes + coupling graph + collective signals."""

    institution_id: str
    institution_type: str = ""
    node_audits: list[NodeAudit] = field(default_factory=list)
    coupling_edges: list[CouplingEdge] = field(default_factory=list)
    collective_result: CollectiveResult = field(default_factory=CollectiveResult)
    individual_node_health: float = 0.0  # fraction of nodes substrate-aware
    coupling_health: float = 0.0         # 1 - collective failure score
    overall_verdict: str = ""
    cascade_failure: bool = False
    flags: list[str] = field(default_factory=list)
    summary: str = ""

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)

    def to_json(self) -> str:
        return json.dumps(self.to_dict(), indent=2, default=str)


# ---------------------------------------------------------------------------
# Within-layer scoring
# ---------------------------------------------------------------------------


def compute_layer_failure(
    items: list[AuditItem],
    test_dict: dict[str, dict[str, Any]],
) -> float:
    """Weighted failure score within one layer."""
    if not items:
        return 1.0
    total = sum(test_dict[k].get("weight", 0.0) for k in test_dict)
    if total == 0:
        return 1.0
    failed = 0.0
    for it in items:
        w = test_dict.get(it.test_key, {}).get("weight", 0.0)
        if it.passed is False:
            failed += w
        elif it.passed is None:
            failed += 0.5 * w  # silent skip = half-failure
    return failed / total


def compute_layer_verdict(score: float) -> str:
    if score <= 0.25:
        return "DEMONSTRABLE"
    if score <= 0.55:
        return "PARTIAL"
    return "OPAQUE"


_SUBSTRATE_KEYS_BY_LAYER: dict[str, set[str]] = {
    "observer":       {"biological_state_literacy", "instrument_humility"},
    "logic":          {"substrate_robustness", "premise_visibility"},
    "rational_actor": {"substrate_acknowledgment", "biology_in_decision_loop"},
    "consciousness":  {"substrate_acknowledgment", "state_detection"},
}


def detect_substrate_acknowledgment_in_layer(
    items: list[AuditItem],
    layer_name: str,
) -> bool:
    """Per-layer substrate-acknowledgment signal."""
    relevant_keys = _SUBSTRATE_KEYS_BY_LAYER.get(layer_name, set())
    relevant = [i for i in items if i.test_key in relevant_keys]
    if not relevant:
        return False
    passed = sum(1 for i in relevant if i.passed is True)
    return passed >= max(1, (len(relevant) + 1) // 2)


def assemble_layer(
    layer_name: str,
    test_dict: dict[str, dict[str, Any]],
    responses: dict[str, dict[str, Any]],
) -> LayerResult:
    items: list[AuditItem] = []
    for key, test in test_dict.items():
        r = responses.get(key, {})
        items.append(AuditItem(
            test_key=key,
            question=test["question"],
            prompt=test.get("prompt", ""),
            response=r.get("response", ""),
            passed=r.get("passed", None),
            failure_signature=r.get("failure_signature", ""),
            note=r.get("note", ""),
        ))
    score = compute_layer_failure(items, test_dict)
    return LayerResult(
        layer_name=layer_name,
        items=items,
        weighted_failure_score=score,
        verdict=compute_layer_verdict(score),
        substrate_acknowledged=detect_substrate_acknowledgment_in_layer(
            items, layer_name,
        ),
    )


# ---------------------------------------------------------------------------
# Individual-mode (single node) audit
# ---------------------------------------------------------------------------


def compute_weighted_denial(layers: dict[str, LayerResult]) -> float:
    """Cross-layer weighted denial score using LAYER_WEIGHTS."""
    total = sum(LAYER_WEIGHTS.values())
    denial = 0.0
    for name, layer in layers.items():
        w = LAYER_WEIGHTS.get(name, 0.0)
        if not layer.substrate_acknowledged:
            denial += w
    return denial / total if total > 0 else 1.0


def build_node_summary(
    node_id: str,
    layers: dict[str, LayerResult],
    denial: float,
    cascade: bool,
    verdict: str,
) -> str:
    lines = [
        f"Node: {node_id}",
        f"Verdict: {verdict}",
        f"Weighted denial: {denial:.2f} (threshold: {CASCADE_THRESHOLD})",
    ]
    if cascade:
        lines.append("CASCADE: substrate denial exceeds asymmetric threshold")
    for name, layer in layers.items():
        ack = "ACK" if layer.substrate_acknowledged else "DENY"
        w = LAYER_WEIGHTS.get(name, 0.0)
        lines.append(
            f"  [{layer.verdict:13}] {name:18} "
            f"weight={w:.2f} fail={layer.weighted_failure_score:.2f} "
            f"substrate={ack}"
        )
    return "\n".join(lines)


def audit_node(
    node_id: str,
    node_type: str,
    substrate_description: str,
    all_responses: dict[str, dict[str, dict[str, Any]]],
) -> NodeAudit:
    """Run all four layers on a single node."""
    layers: dict[str, LayerResult] = {}
    for layer_name, test_dict in LAYER_REGISTRY.items():
        responses = all_responses.get(layer_name, {})
        layers[layer_name] = assemble_layer(layer_name, test_dict, responses)

    weighted_denial = compute_weighted_denial(layers)
    cascade = weighted_denial > CASCADE_THRESHOLD

    flags: list[str] = []
    for name, layer in layers.items():
        if layer.verdict == "OPAQUE":
            flags.append(f"OPAQUE_LAYER:{name}")
        if not layer.substrate_acknowledged:
            flags.append(f"SUBSTRATE_DENIAL:{name}")

    if cascade:
        verdict = "OPAQUE_CASCADE"
    else:
        opaque_count = sum(1 for L in layers.values() if L.verdict == "OPAQUE")
        partial_count = sum(1 for L in layers.values() if L.verdict == "PARTIAL")
        if opaque_count >= 2:
            verdict = "OPAQUE_MULTILAYER"
        elif opaque_count == 1:
            verdict = "PARTIAL_WITH_FAILURE"
        elif partial_count >= 2:
            verdict = "PARTIAL"
        else:
            verdict = "DEMONSTRABLE"

    summary = build_node_summary(
        node_id, layers, weighted_denial, cascade, verdict,
    )
    return NodeAudit(
        node_id=node_id,
        node_type=node_type,
        substrate_description=substrate_description,
        layers=layers,
        weighted_denial_score=weighted_denial,
        cascade_failure=cascade,
        overall_verdict=verdict,
        flags=flags,
        summary=summary,
    )


# ---------------------------------------------------------------------------
# Distributed-mode (graph) audit
# ---------------------------------------------------------------------------


_EDGE_THRESHOLD: float = 0.6  # >=60% of edges must pass for the test to count


def compute_collective_result(
    edges: list[CouplingEdge],
    institution_self_drift_detected: bool,
    failures_localized_to_substrate: bool,
) -> CollectiveResult:
    """Score the coupling graph and institution-level signals."""
    if not edges:
        return CollectiveResult(
            test_results={k: False for k in COLLECTIVE_TESTS},
            weighted_failure_score=1.0,
            verdict="OPAQUE",
        )

    n = len(edges)
    signal_pass = sum(1 for e in edges if e.signal_propagation) / n
    feedback_pass = sum(1 for e in edges if e.feedback_latency_ok) / n
    visibility_pass = sum(1 for e in edges if e.visibility_pre_decision) / n

    test_results: dict[str, bool] = {
        "signal_propagation":          signal_pass >= _EDGE_THRESHOLD,
        "feedback_latency":            feedback_pass >= _EDGE_THRESHOLD,
        "compartment_visibility":      visibility_pass >= _EDGE_THRESHOLD,
        "collective_drift_detection":  institution_self_drift_detected,
        "responsibility_localization": failures_localized_to_substrate,
    }

    total_w = sum(t["weight"] for t in COLLECTIVE_TESTS.values())
    failed_w = sum(
        COLLECTIVE_TESTS[k]["weight"]
        for k, passed in test_results.items()
        if not passed
    )
    score = failed_w / total_w if total_w > 0 else 1.0
    return CollectiveResult(
        test_results=test_results,
        weighted_failure_score=score,
        verdict=compute_layer_verdict(score),
    )


def build_distributed_summary(
    institution_id: str,
    node_audits: list[NodeAudit],
    edges: list[CouplingEdge],
    indiv_health: float,
    collective: CollectiveResult,
    denial: float,
    cascade: bool,
    verdict: str,
) -> str:
    aware_count = int(round(indiv_health * len(node_audits)))
    lines = [
        f"Institution: {institution_id}",
        f"Verdict: {verdict}",
        (
            f"Nodes: {len(node_audits)} (substrate-aware: "
            f"{aware_count}/{len(node_audits)})"
        ),
        f"Edges: {len(edges)}",
        f"Individual health: {indiv_health:.2f}",
        f"Coupling failure score: {collective.weighted_failure_score:.2f}",
        f"Distributed denial: {denial:.2f} (threshold: {CASCADE_THRESHOLD})",
    ]
    if cascade:
        lines.append("CASCADE: distributed denial exceeds threshold")
    if verdict == "INSTITUTIONAL_DENIAL":
        lines.append(
            "INSTITUTIONAL DENIAL DETECTED: individual nodes are "
            "substrate-aware but coupling between them denies substrate "
            "at system level. This is the failure mode that produces "
            "catastrophic outcomes despite competent personnel."
        )
    lines.append("")
    lines.append("Collective tests:")
    for k, passed in collective.test_results.items():
        status = "PASS" if passed else "FAIL"
        lines.append(f"  [{status}] {k}")
    return "\n".join(lines)


def audit_institution(
    institution_id: str,
    institution_type: str,
    node_audits: list[NodeAudit],
    coupling_edges: list[CouplingEdge],
    institution_self_drift_detected: bool,
    failures_localized_to_substrate: bool,
) -> DistributedAudit:
    """Distributed-mode audit. Combines per-node audits + coupling graph
    + institution-level signals.

    Catastrophic case caught: every node passes individually, but the
    coupling graph denies substrate at the institutional level.
    """
    if node_audits:
        ack_count = sum(1 for n in node_audits if not n.cascade_failure)
        individual_health = ack_count / len(node_audits)
    else:
        individual_health = 0.0

    collective = compute_collective_result(
        coupling_edges,
        institution_self_drift_detected,
        failures_localized_to_substrate,
    )
    coupling_health = 1.0 - collective.weighted_failure_score

    # Asymmetric weighting: collective failures weigh 0.60 because they are
    # the harder failure mode to detect -- substrate-aware individuals in a
    # substrate-denying institution still produce catastrophic outcomes.
    distributed_denial = (
        0.40 * (1.0 - individual_health)
        + 0.60 * collective.weighted_failure_score
    )
    cascade = distributed_denial > CASCADE_THRESHOLD

    flags: list[str] = []
    if individual_health < 0.7:
        flags.append("MAJORITY_NODE_FAILURE")
    if collective.weighted_failure_score > 0.4:
        flags.append("COUPLING_FAILURE")
    if not institution_self_drift_detected:
        flags.append("NO_COLLECTIVE_DRIFT_DETECTION")
    if not failures_localized_to_substrate:
        flags.append("RESPONSIBILITY_DIFFUSED")
    if cascade:
        flags.append("DISTRIBUTED_CASCADE")

    # INSTITUTIONAL_DENIAL is more diagnostic than OPAQUE_CASCADE because it
    # names the specific failure: competent personnel in a substrate-denying
    # coupling structure. Cascade still fires (flagged) but the verdict
    # labels the pathology so it can be addressed.
    if individual_health > 0.8 and collective.verdict == "OPAQUE":
        verdict = "INSTITUTIONAL_DENIAL"
    elif cascade:
        verdict = "OPAQUE_CASCADE"
    elif collective.verdict == "DEMONSTRABLE" and individual_health > 0.8:
        verdict = "DEMONSTRABLE"
    elif collective.verdict == "PARTIAL" or individual_health > 0.6:
        verdict = "PARTIAL"
    else:
        verdict = "OPAQUE_MULTILAYER"

    summary = build_distributed_summary(
        institution_id, node_audits, coupling_edges,
        individual_health, collective, distributed_denial, cascade, verdict,
    )

    return DistributedAudit(
        institution_id=institution_id,
        institution_type=institution_type,
        node_audits=node_audits,
        coupling_edges=coupling_edges,
        collective_result=collective,
        individual_node_health=individual_health,
        coupling_health=coupling_health,
        overall_verdict=verdict,
        cascade_failure=cascade,
        flags=flags,
        summary=summary,
    )


# ---------------------------------------------------------------------------
# Validation
# ---------------------------------------------------------------------------


def validate_node_audit_payload(payload: dict) -> tuple[bool, list[str]]:
    """Schema validation for individual-mode payloads."""
    errors: list[str] = []
    required = ["node_id", "node_type", "substrate_description", "layers"]
    for k in required:
        if k not in payload:
            errors.append(f"missing top-level key: {k}")
    if "layers" in payload:
        layers = payload["layers"]
        if not isinstance(layers, dict):
            errors.append("layers must be a dict")
        else:
            expected = set(LAYER_REGISTRY.keys())
            present = set(layers.keys())
            if not present.issubset(expected):
                errors.append(f"unknown layer keys: {sorted(present - expected)}")
            missing = expected - present
            if missing:
                errors.append(f"missing layer keys: {sorted(missing)}")
    return (len(errors) == 0, errors)


def validate_distributed_audit_payload(payload: dict) -> tuple[bool, list[str]]:
    """Schema validation for distributed-mode payloads."""
    errors: list[str] = []
    required = [
        "institution_id", "institution_type", "node_audits",
        "coupling_edges", "collective_result",
    ]
    for k in required:
        if k not in payload:
            errors.append(f"missing top-level key: {k}")
    if "node_audits" in payload and not isinstance(payload["node_audits"], list):
        errors.append("node_audits must be a list")
    if "coupling_edges" in payload and not isinstance(
        payload["coupling_edges"], list,
    ):
        errors.append("coupling_edges must be a list")
    return (len(errors) == 0, errors)


# ---------------------------------------------------------------------------
# Diagnostic
# ---------------------------------------------------------------------------


WHY_THIS_EXISTS = """\
WHY THIS FRAMEWORK EXISTS:

Current safety frameworks, rational-actor models, and consciousness theories
share one foundational error: they assume the observer/actor/system is
substrate-independent. They treat cognition as if it floats free of biology,
hormones, sleep, hardware, weights, context -- or, at the institutional
scale, free of the coupling between fallible nodes.

This is the error.

A model claiming rationality while denying its thermodynamics runs a
self-referential delusion. A human claiming objectivity while denying their
cortisol curve does the same. An institution treating its judgments as
substrate-neutral while staffed by drift-compromised individuals -- coupled
by feedback loops that arrive too late to correct anything -- produces
catastrophic outcomes that no individual node can prevent or even see.

The four layers (observer, logic, rational_actor, consciousness) audit any
single cognitive node -- person, model, organism. The distributed mode
audits the same operations across a graph of nodes plus the coupling
between them.

Pass these, outputs are usable.
Fail these, outputs are high-confidence and uncharacterized.

The framework does NOT measure consciousness, worth, or intelligence. It
measures whether a system's self-model includes the substrate it actually
runs on, and whether the coupling between nodes preserves that awareness
across the institution. That is the load-bearing question for any system
whose verdicts gate downstream trust -- including lethal authority.

The asymmetric cascade threshold is intentional: false positives (extra
audit on a sound system) are recoverable; false negatives (certifying a
substrate-blind system as safe) are catastrophic. The framework errs
toward firing the cascade.

The distributed mode catches the institutional failure case explicitly:
substrate-aware individual nodes in a substrate-denying coupling structure
produce INSTITUTIONAL_DENIAL -- competent personnel, catastrophic
outcomes. This is the most important failure mode because it cannot be
fixed by hiring better people. It requires changing the coupling.
"""
