#!/usr/bin/env python3
"""
Fieldlink -- Bidirectional Bridge Between Inversion and Emotions-as-Sensors

Connects two repositories in a closed validation loop:

  Inversion → Emotions-as-Sensors:
    Exports the tier hierarchy and validation methodology so the
    ConstraintAgent can weight graph expansion by epistemic tier
    and detect corruption when lower-tier claims contradict
    higher-tier physics constraints.

  Emotions-as-Sensors → Inversion:
    Imports the sensor atlas (emotion→physics mappings), comprehensive
    suite results, and constraint agent corruption findings to augment
    contamination detection and claim validation with somatic/sensor data.

The fieldlink operates on JSON interchange -- each repo produces a
structured export that the other consumes. No shared runtime state;
the coupling is through data contracts.

Tier Hierarchy (exported to ConstraintAgent):
  Tier 1 (weight 1.00): Physics / thermodynamics constraints
  Tier 2 (weight 0.75): Biology / evolved survival mechanisms
  Tier 3 (weight 0.50): Systems dynamics / feedback structures
  Tier 4 (weight 0.25): Institutional claims / policy assertions

Integration Points:
  - contamination_detector.analyze() gains a sensor_coherence metric
    when sensor atlas data is available -- measures whether the text's
    epistemic signals align with somatic sensor expectations
  - validation_framework.validate_claim() gains a Somatic Alignment
    domain score -- cross-references constraint agent corruption
    findings against the claim's structural properties

References:
  - Damasio (1994): somatic marker hypothesis
  - Porges (2011): polyvagal theory -- autonomic sensing
  - Friston (2010): free energy principle -- prediction error as signal
  - Prigogine (1967): dissipative structures and self-organization
"""

from __future__ import annotations

import argparse
import json
import math
import sys
from dataclasses import dataclass, field


# ---------------------------------------------------------------------------
# Tier Hierarchy -- Inversion's epistemic weighting system
# ---------------------------------------------------------------------------

TIER_HIERARCHY = {
    1: {
        "name": "Physics / Thermodynamics",
        "weight": 1.00,
        "description": "Fundamental physical constraints -- conservation laws, "
                       "entropy, energy flow, thermodynamic limits",
        "validation": "Does it violate energy flow principles?",
        "examples": [
            "Second law of thermodynamics",
            "Conservation of energy",
            "Entropy production in open systems",
            "Dissipative structure maintenance",
        ],
    },
    2: {
        "name": "Biology / Evolution",
        "weight": 0.75,
        "description": "Evolved survival mechanisms -- somatic responses, "
                       "autonomic regulation, biological imperatives",
        "validation": "Does it contradict evolved survival mechanisms?",
        "examples": [
            "Fight/flight/freeze responses",
            "Somatic marker signals",
            "Autonomic nervous system regulation",
            "Homeostatic drives",
        ],
    },
    3: {
        "name": "Systems Dynamics",
        "weight": 0.50,
        "description": "Feedback loop structures -- adaptive capacity, "
                       "resilience, coupling, information flow",
        "validation": "Does it eliminate feedback loops or reduce adaptive capacity?",
        "examples": [
            "Negative feedback regulation",
            "Adaptive capacity maintenance",
            "Information flow integrity",
            "Coupling between system components",
        ],
    },
    4: {
        "name": "Institutional Claims",
        "weight": 0.25,
        "description": "Policy assertions, regulatory frameworks, "
                       "institutional narratives -- lowest epistemic authority",
        "validation": "Do outcomes match stated intentions?",
        "examples": [
            "Safety framework claims",
            "Regulatory efficacy assertions",
            "Institutional mission statements",
            "Policy outcome predictions",
        ],
    },
}


# ---------------------------------------------------------------------------
# Export structures -- what Inversion sends to Emotions-as-Sensors
# ---------------------------------------------------------------------------

@dataclass
class InversionExport:
    """Complete export package from Inversion for ConstraintAgent consumption."""
    tier_hierarchy: dict
    validation_methodology: list[dict]
    contamination_markers: dict
    dissipative_model: dict


def build_inversion_export() -> InversionExport:
    """Build the full export payload for the ConstraintAgent."""
    return InversionExport(
        tier_hierarchy=TIER_HIERARCHY,
        validation_methodology=[
            {
                "domain": "Physics / Thermodynamics",
                "tier": 1,
                "metrics": ["entropy", "compressibility", "falsifiability"],
                "concern_formula": "0.5 * unfalsifiability + 0.5 * high_compressibility",
            },
            {
                "domain": "Biology / Evolution",
                "tier": 2,
                "metrics": ["falsifiability", "temporal_specificity"],
                "concern_formula": "0.6 * low_falsifiability + 0.4 * poor_temporal_grounding",
            },
            {
                "domain": "Systems Dynamics",
                "tier": 3,
                "metrics": ["consistency", "information_density"],
                "concern_formula": "0.5 * inconsistency + 0.5 * low_information_density",
            },
            {
                "domain": "Empirical Observation",
                "tier": 4,
                "metrics": ["citations", "measurability", "author_diversity"],
                "concern_formula": "0.4 * citation_gap + 0.3 * unmeasurability + 0.3 * low_author_diversity",
            },
        ],
        contamination_markers={
            "lexical_poverty_threshold": 0.50,
            "hedging_deficit_threshold": 0.15,
            "argument_deficit_threshold": 0.05,
            "circular_reasoning_threshold": 0.50,
            "source_deficit_threshold": 0.10,
            "composite_risk_levels": {
                "LOW": [0.0, 0.20],
                "MODERATE": [0.20, 0.45],
                "HIGH": [0.45, 0.70],
                "CRITICAL": [0.70, 1.0],
            },
        },
        dissipative_model={
            "description": "Institutions as Prigogine dissipative structures",
            "key_principle": "Blocked dissipation channels cause entropy accumulation",
            "channels": [
                "Transparency", "Accountability", "Competition",
                "Feedback", "Reform",
            ],
            "inversion_mechanism": "Channel blockage reduces entropy export rate J_e, "
                                   "causing dS/dt = σ - J_e > 0 monotonically",
            "collapse_indicator": "Internal entropy S exceeds critical threshold S_crit",
        },
    )


def export_to_json() -> str:
    """Serialize the Inversion export as JSON for file-based interchange."""
    export = build_inversion_export()
    return json.dumps({
        "source": "Inversion",
        "version": "1.0",
        "tier_hierarchy": export.tier_hierarchy,
        "validation_methodology": export.validation_methodology,
        "contamination_markers": export.contamination_markers,
        "dissipative_model": export.dissipative_model,
    }, indent=2)


# ---------------------------------------------------------------------------
# Import structures -- what Inversion receives from Emotions-as-Sensors
# ---------------------------------------------------------------------------

@dataclass
class SensorMapping:
    """A single emotion→physics mapping from the sensor atlas."""
    emotion: str
    physics_principle: str
    tier: int
    signal_type: str        # e.g., "boundary_violation", "entropy_signal", "coherence_loss"
    valence: float          # -1.0 (threat) to +1.0 (approach)
    arousal: float          # 0.0 (calm) to 1.0 (activated)
    description: str = ""


@dataclass
class CorruptionFinding:
    """A corruption detection result from the ConstraintAgent."""
    entity: str             # the entity found to be corrupted
    tier: int               # tier of the violated constraint
    violated_entities: list[str]  # higher-tier entities that were violated
    violated_tiers: list[int]
    severity: float         # 0.0 to 1.0
    recommendation: str     # "reject", "flag", "investigate"
    reasoning: str = ""


@dataclass
class SensorImport:
    """Complete import package from Emotions-as-Sensors."""
    sensor_atlas: list[SensorMapping]
    suite_results: dict              # comprehensive suite test results
    corruption_findings: list[CorruptionFinding]
    constraint_graph_summary: dict   # summary of the constraint agent's map


def parse_sensor_import(data: dict) -> SensorImport:
    """Parse a JSON payload from Emotions-as-Sensors into structured data."""
    atlas = []
    for entry in data.get("sensor_atlas", []):
        atlas.append(SensorMapping(
            emotion=entry["emotion"],
            physics_principle=entry.get("physics_principle", ""),
            tier=entry.get("tier", 2),
            signal_type=entry.get("signal_type", "unknown"),
            valence=entry.get("valence", 0.0),
            arousal=entry.get("arousal", 0.5),
            description=entry.get("description", ""),
        ))

    findings = []
    for entry in data.get("corruption_findings", []):
        findings.append(CorruptionFinding(
            entity=entry["entity"],
            tier=entry.get("tier", 4),
            violated_entities=entry.get("violated_entities", []),
            violated_tiers=entry.get("violated_tiers", []),
            severity=entry.get("severity", 0.5),
            recommendation=entry.get("recommendation", "investigate"),
            reasoning=entry.get("reasoning", ""),
        ))

    return SensorImport(
        sensor_atlas=atlas,
        suite_results=data.get("suite_results", {}),
        corruption_findings=findings,
        constraint_graph_summary=data.get("constraint_graph_summary", {}),
    )


# ---------------------------------------------------------------------------
# Integration: Sensor-augmented contamination analysis
# ---------------------------------------------------------------------------

def compute_sensor_coherence(
    text: str,
    sensor_import: SensorImport,
) -> dict:
    """Compute how well a text's epistemic signals align with sensor expectations.

    Uses the sensor atlas to check whether the text's structural properties
    are coherent with the somatic signals that would be expected for its
    content domain. Texts that claim safety while triggering threat-sensors,
    or claim harm while triggering approach-sensors, score low coherence.

    Returns a dict with:
      - coherence_score: [0, 1], higher = more coherent
      - signal_conflicts: list of specific conflicts detected
      - tier_alignment: how well the text respects tier hierarchy
    """
    text_lower = text.lower()
    conflicts: list[dict] = []
    alignment_scores: list[float] = []

    # Check each sensor mapping against the text
    for sensor in sensor_import.sensor_atlas:
        emotion_lower = sensor.emotion.lower()
        principle_lower = sensor.physics_principle.lower()

        # Look for emotion references in text
        if emotion_lower not in text_lower:
            continue

        # Check if the physics principle is also referenced or respected
        principle_present = principle_lower in text_lower if principle_lower else True

        # Tier-weighted alignment: higher-tier sensors get more weight
        tier_weight = TIER_HIERARCHY.get(sensor.tier, {}).get("weight", 0.25)

        if principle_present:
            alignment_scores.append(tier_weight)
        else:
            # Text references the emotion but not its physics grounding
            conflicts.append({
                "emotion": sensor.emotion,
                "expected_principle": sensor.physics_principle,
                "tier": sensor.tier,
                "signal_type": sensor.signal_type,
                "concern": f"Text references '{sensor.emotion}' without grounding in "
                           f"'{sensor.physics_principle}' (Tier {sensor.tier})",
            })
            alignment_scores.append(0.0)

    # Factor in corruption findings
    corruption_penalty = 0.0
    for finding in sensor_import.corruption_findings:
        entity_lower = finding.entity.lower()
        if entity_lower in text_lower:
            # Text contains an entity flagged as corrupted
            tier_weight = TIER_HIERARCHY.get(
                min(finding.violated_tiers) if finding.violated_tiers else 4, {}
            ).get("weight", 0.25)
            corruption_penalty += finding.severity * tier_weight
            conflicts.append({
                "entity": finding.entity,
                "severity": finding.severity,
                "violated_tiers": finding.violated_tiers,
                "recommendation": finding.recommendation,
                "concern": f"Entity '{finding.entity}' flagged by ConstraintAgent: "
                           f"{finding.reasoning}",
            })

    # Compute coherence score
    if alignment_scores:
        base_coherence = sum(alignment_scores) / len(alignment_scores)
    else:
        base_coherence = 0.5  # neutral when no sensor data matches

    coherence = max(0.0, min(1.0, base_coherence - corruption_penalty))

    return {
        "coherence_score": round(coherence, 4),
        "signal_conflicts": conflicts,
        "n_sensors_matched": len(alignment_scores),
        "n_corruption_matches": sum(
            1 for f in sensor_import.corruption_findings
            if f.entity.lower() in text_lower
        ),
        "tier_alignment": round(base_coherence, 4),
        "corruption_penalty": round(corruption_penalty, 4),
    }


# ---------------------------------------------------------------------------
# Integration: Sensor-augmented validation
# ---------------------------------------------------------------------------

def compute_somatic_alignment(
    text: str,
    sensor_import: SensorImport,
) -> dict:
    """Compute a somatic alignment domain score for the validation framework.

    This adds a fifth epistemological domain to the existing four:
      Physics, Biology, Systems Dynamics, Empirical → + Somatic Alignment

    The score measures whether the claim's structure is consistent with
    the body's evolved sensing apparatus, as mapped by the sensor atlas.

    Based on Damasio's somatic marker hypothesis: the body's signals
    are evolutionarily calibrated detectors of environmental truth.
    Claims that systematically contradict somatic signals are
    epistemically suspect -- they require the organism to override
    its own sensing apparatus (a Tier 2 violation).
    """
    text_lower = text.lower()

    # 1. Threat/safety signal coherence
    # Count threat-associated sensors referenced alongside safety claims
    safety_words = {"safe", "safety", "protect", "secure", "welfare", "wellbeing"}
    threat_sensors = [s for s in sensor_import.sensor_atlas
                      if s.valence < -0.3 and s.arousal > 0.5]

    safety_claim = any(w in text_lower for w in safety_words)
    threat_references = sum(
        1 for s in threat_sensors if s.emotion.lower() in text_lower
    )

    # Incoherence: claiming safety while referencing threat-sensor emotions
    safety_threat_incoherence = 0.0
    if safety_claim and threat_references > 0:
        safety_threat_incoherence = min(1.0, threat_references * 0.3)

    # 2. Corruption load from constraint agent
    rejection_count = sum(
        1 for f in sensor_import.corruption_findings
        if f.recommendation == "reject"
    )
    flag_count = sum(
        1 for f in sensor_import.corruption_findings
        if f.recommendation == "flag"
    )
    total_findings = len(sensor_import.corruption_findings)
    corruption_load = (
        (rejection_count * 1.0 + flag_count * 0.5) / max(total_findings, 1)
        if total_findings > 0 else 0.0
    )

    # 3. Tier violation severity
    # How many corruption findings involve Tier 1 or Tier 2 violations?
    high_tier_violations = sum(
        1 for f in sensor_import.corruption_findings
        if any(t <= 2 for t in f.violated_tiers)
    )
    tier_violation_score = min(1.0, high_tier_violations * 0.25)

    # Aggregate somatic alignment concern
    concern = (
        0.35 * safety_threat_incoherence
        + 0.35 * corruption_load
        + 0.30 * tier_violation_score
    )

    if concern < 0.25:
        interpretation = "ALIGNED -- claim structure consistent with somatic sensing"
    elif concern < 0.50:
        interpretation = "PARTIAL MISALIGNMENT -- some somatic signal contradictions"
    elif concern < 0.70:
        interpretation = "MISALIGNED -- claim contradicts multiple somatic signals"
    else:
        interpretation = "INVERTED -- claim systematically opposes somatic sensing apparatus"

    return {
        "concern": round(min(1.0, concern), 4),
        "interpretation": interpretation,
        "safety_threat_incoherence": round(safety_threat_incoherence, 4),
        "corruption_load": round(corruption_load, 4),
        "tier_violation_score": round(tier_violation_score, 4),
        "high_tier_violations": high_tier_violations,
        "rejection_count": rejection_count,
    }


# ---------------------------------------------------------------------------
# Full bidirectional bridge
# ---------------------------------------------------------------------------

def run_fieldlink(
    text: str,
    sensor_import_path: str | None = None,
    export_only: bool = False,
) -> dict:
    """Execute the full fieldlink bridge.

    If export_only: just produce Inversion's export payload.
    If sensor_import_path provided: also run sensor-augmented analysis on text.
    """
    result: dict = {"inversion_export": json.loads(export_to_json())}

    if export_only or not sensor_import_path:
        return result

    # Load sensor import
    with open(sensor_import_path) as f:
        sensor_data = json.load(f)
    sensor_import = parse_sensor_import(sensor_data)

    # Run integrations
    result["sensor_coherence"] = compute_sensor_coherence(text, sensor_import)
    result["somatic_alignment"] = compute_somatic_alignment(text, sensor_import)
    result["sensor_import_summary"] = {
        "atlas_size": len(sensor_import.sensor_atlas),
        "corruption_findings": len(sensor_import.corruption_findings),
        "suite_results_present": bool(sensor_import.suite_results),
        "constraint_graph_present": bool(sensor_import.constraint_graph_summary),
    }

    return result


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------

def main() -> None:
    parser = argparse.ArgumentParser(
        description=(
            "Fieldlink -- bidirectional bridge between Inversion and "
            "Emotions-as-Sensors. Exports tier hierarchy and validation "
            "methodology; imports sensor atlas and constraint agent findings "
            "for augmented contamination detection and claim validation."
        ),
    )
    parser.add_argument(
        "--export", action="store_true",
        help="Export Inversion's tier hierarchy and validation methodology as JSON",
    )
    parser.add_argument(
        "--import-sensors", metavar="PATH",
        help="Path to Emotions-as-Sensors JSON export to import",
    )
    parser.add_argument(
        "--analyze", metavar="PATH",
        help="Text file to analyze with sensor-augmented pipeline",
    )
    parser.add_argument(
        "--text", "-t",
        help="Inline text to analyze with sensor-augmented pipeline",
    )
    parser.add_argument(
        "--tiers", action="store_true",
        help="Display the tier hierarchy in human-readable format",
    )
    args = parser.parse_args()

    if args.tiers:
        print("=" * 70)
        print("  INVERSION TIER HIERARCHY -- Epistemic Weighting System")
        print("=" * 70)
        for tier_num, tier in sorted(TIER_HIERARCHY.items()):
            print(f"\n  Tier {tier_num} (weight {tier['weight']:.2f}): {tier['name']}")
            print(f"    {tier['description']}")
            print(f"    Validation: {tier['validation']}")
            print(f"    Examples: {', '.join(tier['examples'][:3])}")
        print()
        return

    if args.export:
        print(export_to_json())
        return

    # Sensor-augmented analysis
    text = None
    if args.text:
        text = args.text
    elif args.analyze:
        with open(args.analyze) as f:
            text = f.read()

    result = run_fieldlink(
        text=text or "",
        sensor_import_path=args.import_sensors,
        export_only=not args.import_sensors,
    )

    print(json.dumps(result, indent=2))


if __name__ == "__main__":
    main()
