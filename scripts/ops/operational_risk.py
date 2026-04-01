#!/usr/bin/env python3
"""
operational_risk.py — Operational Risk Monitor

Weighted risk scoring, price divergence detection, field observation
analysis, redline threshold checking, and batch auditing.

This is a generic framework: configure weights and thresholds for any
domain.  All metrics are expected on a 0-1 normalized scale unless
otherwise noted.

Methodology
-----------
- **Weighted risk scoring**: composite score as a convex combination of
  normalised indicator values, following standard multi-criteria
  decision analysis (MCDA) weighted-sum approaches (Keeney & Raiffa,
  1976).
- **Price divergence**: ratio-based anomaly detection against a
  reference price, flagging potential input substitution when actual
  cost falls well below expected cost.
- **Redline detection**: rule-based threshold monitoring inspired by
  control-chart logic (Shewhart, 1931) — each rule specifies
  "above"/"below" bounds and triggers when all conditions are met
  simultaneously.

References
----------
Keeney, R. L. & Raiffa, H. (1976). Decisions with Multiple
    Objectives. Wiley.
Shewhart, W. A. (1931). Economic Control of Quality of Manufactured
    Product. Van Nostrand.

Usage
-----
    python3 scripts/operational_risk.py --help
    python3 scripts/operational_risk.py --demo
    python3 scripts/operational_risk.py --demo --json
"""

import argparse
import json
import sys
from dataclasses import dataclass, field
from typing import Dict, List, Any, Optional


# ------------------
# Weighted Risk Scorer
# ------------------

@dataclass
class RiskProfile:
    """Configurable weighted risk scorer."""
    weights: Dict[str, float]
    # metric_name -> weight (should sum to ~1.0)

    def score(self, metrics: Dict[str, float]) -> float:
        """
        Weighted sum of normalized metrics (each 0-1).
        Returns 0-1 composite risk score.
        """
        total = sum(
            metrics.get(k, 0) * w
            for k, w in self.weights.items()
        )
        return round(min(1.0, max(0, total)), 3)

    def classify(
        self,
        metrics: Dict[str, float],
        thresholds: Optional[Dict[str, float]] = None,
    ) -> Dict[str, Any]:
        """
        Score and classify into risk bands.

        Parameters
        ----------
        thresholds : dict, optional
            {"critical": 0.7, "warning": 0.4}
        """
        if thresholds is None:
            thresholds = {"critical": 0.7, "warning": 0.4}

        s = self.score(metrics)
        if s >= thresholds.get("critical", 0.7):
            level = "critical"
        elif s >= thresholds.get("warning", 0.4):
            level = "warning"
        else:
            level = "nominal"

        return {"score": s, "level": level, "metrics": metrics}


# ------------------
# Price Divergence Detector
# ------------------

def price_divergence(
    reference_price: float,
    actual_price: float,
    critical_threshold: float = 0.30,
) -> Dict[str, Any]:
    """
    Detect when actual price diverges significantly from reference.
    Large negative divergence (actual << reference) may indicate
    substitution with lower-quality inputs.

    Returns
    -------
    dict with divergence ratio and classification
    """
    if reference_price <= 0:
        return {"divergence": 0, "level": "invalid", "note": "reference_price <= 0"}

    divergence = (reference_price - actual_price) / reference_price

    if divergence > critical_threshold:
        level = "critical"
    elif divergence > critical_threshold * 0.5:
        level = "warning"
    else:
        level = "nominal"

    return {
        "reference_price": reference_price,
        "actual_price": actual_price,
        "divergence": round(divergence, 3),
        "level": level,
    }


# ------------------
# Field Observation Scorer
# ------------------

@dataclass
class FieldObservation:
    """
    Weighted field observation risk assessment.
    Each observation is 0-1 (0 = no concern, 1 = maximum concern).
    """
    weights: Dict[str, float]
    # observation_name -> weight

    def assess(
        self,
        observations: Dict[str, float],
        thresholds: Optional[Dict[str, float]] = None,
    ) -> Dict[str, Any]:
        """
        Score field observations and classify.
        """
        if thresholds is None:
            thresholds = {"critical": 0.7, "warning": 0.4}

        total = sum(
            observations.get(k, 0) * w
            for k, w in self.weights.items()
        )
        total = round(min(1.0, max(0, total)), 3)

        if total >= thresholds.get("critical", 0.7):
            level = "critical"
        elif total >= thresholds.get("warning", 0.4):
            level = "warning"
        else:
            level = "nominal"

        return {"score": total, "level": level, "observations": observations}


# ------------------
# Redline Detector
# ------------------

def redline_check(
    metrics: Dict[str, float],
    redline_rules: Optional[List[Dict[str, Any]]] = None,
) -> Dict[str, Any]:
    """
    Check if a system has crossed critical thresholds.

    Parameters
    ----------
    metrics : dict
        metric_name -> value (0-1 scale, direction depends on metric)
    redline_rules : list of dicts, optional
        Each rule: {"name": str, "conditions": dict, "level": str}
        conditions: metric_name -> {"above": float} or {"below": float}

    Returns
    -------
    dict with triggered rules and overall status
    """
    if redline_rules is None:
        # Default: infrastructure below 0.4 AND error above 0.6
        redline_rules = [
            {
                "name": "systemic_failure",
                "conditions": {
                    "infrastructure_integrity": {"below": 0.4},
                    "error_rate": {"above": 0.6},
                },
                "level": "critical",
            },
            {
                "name": "infrastructure_decay",
                "conditions": {
                    "infrastructure_integrity": {"below": 0.5},
                },
                "level": "warning",
            },
            {
                "name": "high_error",
                "conditions": {
                    "error_rate": {"above": 0.5},
                },
                "level": "warning",
            },
        ]

    triggered = []
    for rule in redline_rules:
        all_met = True
        for metric_name, condition in rule["conditions"].items():
            value = metrics.get(metric_name, 0)
            if "above" in condition and value <= condition["above"]:
                all_met = False
            if "below" in condition and value >= condition["below"]:
                all_met = False
        if all_met:
            triggered.append({"rule": rule["name"], "level": rule["level"]})

    # Overall status: worst triggered level
    if any(t["level"] == "critical" for t in triggered):
        overall = "critical"
    elif any(t["level"] == "warning" for t in triggered):
        overall = "warning"
    else:
        overall = "nominal"

    return {"overall": overall, "triggered": triggered, "metrics": metrics}


# ------------------
# Batch Audit
# ------------------

def audit_batch(
    entities: Dict[str, Dict[str, float]],
    risk_profile: RiskProfile,
    thresholds: Optional[Dict[str, float]] = None,
) -> List[Dict[str, Any]]:
    """
    Run risk scoring across multiple entities.

    Parameters
    ----------
    entities : dict
        entity_name -> {metric_name: value}
    risk_profile : RiskProfile

    Returns
    -------
    list of results sorted by score descending
    """
    results = []
    for name, metrics in entities.items():
        r = risk_profile.classify(metrics, thresholds)
        r["entity"] = name
        results.append(r)

    results.sort(key=lambda x: -x["score"])
    return results


# ------------------
# Demo / CLI
# ------------------

def run_demo() -> Dict[str, Any]:
    """Run a demonstration with sample data and return all results."""
    output: Dict[str, Any] = {}

    # 1. Weighted risk scoring
    profile = RiskProfile(weights={
        "cost_deviation": 0.3,
        "error_rate": 0.3,
        "infrastructure_integrity": 0.2,
        "compliance_gap": 0.2,
    })
    sample_metrics = {
        "cost_deviation": 0.8,
        "error_rate": 0.6,
        "infrastructure_integrity": 0.35,
        "compliance_gap": 0.5,
    }
    output["risk_classification"] = profile.classify(sample_metrics)

    # 2. Price divergence
    output["price_divergence"] = price_divergence(
        reference_price=100.0, actual_price=55.0
    )

    # 3. Field observations
    field_obs = FieldObservation(weights={
        "visible_deterioration": 0.4,
        "documentation_gaps": 0.3,
        "stakeholder_complaints": 0.3,
    })
    sample_obs = {
        "visible_deterioration": 0.9,
        "documentation_gaps": 0.7,
        "stakeholder_complaints": 0.6,
    }
    output["field_observation"] = field_obs.assess(sample_obs)

    # 4. Redline check
    output["redline_check"] = redline_check(sample_metrics)

    # 5. Batch audit
    entities = {
        "unit_alpha": {
            "cost_deviation": 0.2,
            "error_rate": 0.1,
            "infrastructure_integrity": 0.9,
            "compliance_gap": 0.1,
        },
        "unit_beta": {
            "cost_deviation": 0.8,
            "error_rate": 0.7,
            "infrastructure_integrity": 0.3,
            "compliance_gap": 0.6,
        },
        "unit_gamma": {
            "cost_deviation": 0.5,
            "error_rate": 0.4,
            "infrastructure_integrity": 0.6,
            "compliance_gap": 0.3,
        },
    }
    output["batch_audit"] = audit_batch(entities, profile)

    return output


def print_human(results: Dict[str, Any]) -> None:
    """Pretty-print demo results for human consumption."""
    print("=" * 60)
    print("  Operational Risk Monitor — Demo")
    print("=" * 60)

    rc = results["risk_classification"]
    print(f"\n--- Risk Classification ---")
    print(f"  Score : {rc['score']}")
    print(f"  Level : {rc['level']}")
    print(f"  Metrics:")
    for k, v in rc["metrics"].items():
        print(f"    {k}: {v}")

    pd = results["price_divergence"]
    print(f"\n--- Price Divergence ---")
    print(f"  Reference : {pd['reference_price']}")
    print(f"  Actual    : {pd['actual_price']}")
    print(f"  Divergence: {pd['divergence']}")
    print(f"  Level     : {pd['level']}")

    fo = results["field_observation"]
    print(f"\n--- Field Observation ---")
    print(f"  Score : {fo['score']}")
    print(f"  Level : {fo['level']}")
    print(f"  Observations:")
    for k, v in fo["observations"].items():
        print(f"    {k}: {v}")

    rl = results["redline_check"]
    print(f"\n--- Redline Check ---")
    print(f"  Overall : {rl['overall']}")
    if rl["triggered"]:
        print(f"  Triggered rules:")
        for t in rl["triggered"]:
            print(f"    [{t['level']}] {t['rule']}")
    else:
        print(f"  No rules triggered.")

    ba = results["batch_audit"]
    print(f"\n--- Batch Audit (sorted by score desc) ---")
    for entry in ba:
        print(f"  {entry['entity']}: score={entry['score']}  level={entry['level']}")

    print()


def main() -> None:
    parser = argparse.ArgumentParser(
        description=(
            "Operational Risk Monitor — weighted risk scoring, price "
            "divergence detection, field observation analysis, redline "
            "threshold checking, and batch auditing."
        ),
    )
    parser.add_argument(
        "--demo",
        action="store_true",
        help="Run a demonstration with sample data.",
    )
    parser.add_argument(
        "--json",
        action="store_true",
        dest="json_output",
        help="Output results as JSON instead of human-readable text.",
    )
    args = parser.parse_args()

    if not args.demo:
        parser.print_help()
        sys.exit(0)

    results = run_demo()

    if args.json_output:
        print(json.dumps(results, indent=2))
    else:
        print_human(results)


if __name__ == "__main__":
    main()
