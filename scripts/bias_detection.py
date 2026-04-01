#!/usr/bin/env python3
"""
Bias Detection -- Six Sigma DMAIC Layer 2: Design Choice Accountability

Layer 1 audits the mechanics: "Does this code work correctly?"
Layer 2 audits the choices: "Why was this code written THIS way?"

Catches human bias (domain assumptions, cultural defaults) and AI bias
(optimization tendency, recency weighting, complexity preference).

Components:
  - KNOWN_BIAS_PATTERNS: 8 documented bias types with indicators
  - DesignChoice: tracks what was chosen, what alternatives exist, who decided
  - flag_biases(): scans parameters, assumptions, and design choices for bias
  - compare_formulations(): runs the same audit on alternative formulations

References:
  - Ioannidis (2005): why most published research findings are false
  - Kahneman (2011): Thinking, Fast and Slow -- cognitive biases
  - Saltelli (2020): Ethics of quantification
"""

from __future__ import annotations

import os
import sys
from dataclasses import dataclass
from typing import Any, Callable, Dict, List, Optional, Tuple

# Allow running as script or module
if not __package__:
    sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from scripts.audit_core import (
    AssumptionRecord,
    ParameterSpec,
    monte_carlo_capability,
    sensitivity_analysis,
)


# =========================================================================
# Known Bias Patterns
# =========================================================================

KNOWN_BIAS_PATTERNS = {
    "optimization_bias": {
        "description": "Tendency to frame all systems as optimization problems",
        "indicators": [
            "Single objective function without constraints",
            "Parameters chosen to maximize one output",
            "No accounting for what is sacrificed",
        ],
        "common_in": ["AI models", "economics", "industrial engineering"],
    },
    "recency_bias": {
        "description": "Over-weighting recent data or methods over established physics",
        "indicators": [
            "Default values from recent papers only",
            "No comparison to long-term baselines",
            "Ignoring pre-industrial or indigenous approaches",
        ],
        "common_in": ["AI models", "policy analysis"],
    },
    "complexity_bias": {
        "description": "Preferring complex models when simpler ones explain the data",
        "indicators": [
            "More parameters than the system requires",
            "Nested functions without clear physical justification",
            "Sensitivity analysis shows most parameters don't matter",
        ],
        "common_in": ["AI models", "academic research"],
    },
    "simplification_bias": {
        "description": "Dropping terms that are inconvenient to model",
        "indicators": [
            "Externalized costs set to zero",
            "Long-term feedback loops omitted",
            "Coupling terms between subsystems missing",
        ],
        "common_in": ["industrial models", "economic models"],
    },
    "linearity_bias": {
        "description": "Assuming linear relationships where nonlinear dynamics exist",
        "indicators": [
            "All rates are constant",
            "No threshold or saturation effects",
            "No feedback between state variables",
        ],
        "common_in": ["AI models", "spreadsheet analysis"],
    },
    "survivorship_bias": {
        "description": "Training on successful systems, ignoring failed ones",
        "indicators": [
            "Default parameters reflect 'best case'",
            "No failure mode in the model",
            "Validation only against working examples",
        ],
        "common_in": ["AI models", "business analysis"],
    },
    "scale_bias": {
        "description": "Assuming results at one scale apply at another",
        "indicators": [
            "No scale parameter in the model",
            "Same equations for lab and field",
            "No spatial or temporal resolution check",
        ],
        "common_in": ["AI models", "engineering extrapolation"],
    },
    "externalization_bias": {
        "description": "Omitting costs borne by parties outside the model boundary",
        "indicators": [
            "No pollution, waste, or degradation terms",
            "Efficiency calculated without full lifecycle",
            "System boundary excludes downstream effects",
        ],
        "common_in": ["industrial models", "economic models", "AI trained on corporate data"],
    },
}


# =========================================================================
# Design Choice Record
# =========================================================================

@dataclass
class DesignChoice:
    """Documents a specific modeling decision.

    Forces the modeler to state what alternatives existed
    and why this one was chosen.
    """
    name: str
    chosen: str
    alternatives: List[str]
    reason: str
    bias_risk: List[str]
    impact_on_output: str = ""
    who_decided: str = ""


# =========================================================================
# Bias Flag Engine
# =========================================================================

def flag_biases(
    specs: List[ParameterSpec],
    assumptions: List[AssumptionRecord],
    design_choices: List[DesignChoice],
    sensitivity_result: Optional[Dict] = None,
) -> List[Dict[str, Any]]:
    """Scan parameters, assumptions, and design choices for known bias patterns.

    Returns list of bias flags with evidence and severity.
    """
    flags: List[Dict[str, Any]] = []

    # Check parameters
    undocumented_sources = [s for s in specs if s.source in ("assumed", "")]
    if len(undocumented_sources) > len(specs) * 0.3:
        flags.append({
            "bias": "simplification_bias",
            "evidence": f"{len(undocumented_sources)}/{len(specs)} parameters assumed or undocumented",
            "severity": "high",
            "recommendation": "Trace each parameter to measurement or derivation",
        })

    all_derived = all(s.source == "derived" for s in specs if s.source)
    if all_derived and len(specs) > 3:
        flags.append({
            "bias": "complexity_bias",
            "evidence": "All parameters derived -- no direct measurements anchor the model",
            "severity": "medium",
            "recommendation": "Include at least one directly measured parameter as ground truth",
        })

    # Check assumptions
    unfalsifiable = [a for a in assumptions if not a.falsifiable]
    if unfalsifiable:
        flags.append({
            "bias": "survivorship_bias",
            "evidence": f"{len(unfalsifiable)} unfalsifiable assumptions: {[a.name for a in unfalsifiable]}",
            "severity": "high",
            "recommendation": "Every assumption must have a falsification test",
        })

    no_test = [a for a in assumptions if a.falsifiable and not a.falsification_test]
    if no_test:
        flags.append({
            "bias": "simplification_bias",
            "evidence": f"{len(no_test)} assumptions lack falsification tests: {[a.name for a in no_test]}",
            "severity": "medium",
            "recommendation": "Define specific observations that would prove each assumption wrong",
        })

    physics_basis = [a for a in assumptions if a.basis == "physics"]
    convention_basis = [a for a in assumptions if a.basis == "convention"]
    if len(convention_basis) > len(physics_basis):
        flags.append({
            "bias": "recency_bias",
            "evidence": f"More assumptions based on convention ({len(convention_basis)}) than physics ({len(physics_basis)})",
            "severity": "medium",
            "recommendation": "Derive from first principles where possible",
        })

    # Check design choices
    for dc in design_choices:
        if not dc.alternatives:
            flags.append({
                "bias": "optimization_bias",
                "evidence": f"Design choice '{dc.name}' lists no alternatives -- was only one option considered?",
                "severity": "high",
                "recommendation": "Document at least 2 alternative formulations",
            })

        for bias_name in dc.bias_risk:
            if bias_name in KNOWN_BIAS_PATTERNS:
                pattern = KNOWN_BIAS_PATTERNS[bias_name]
                flags.append({
                    "bias": bias_name,
                    "evidence": f"Design choice '{dc.name}' self-identified as susceptible: {pattern['description']}",
                    "severity": "medium",
                    "source": dc.who_decided,
                    "recommendation": f"Test alternative formulations: {dc.alternatives[:2]}",
                })

    # Check sensitivity results for complexity bias
    if sensitivity_result:
        pareto = sensitivity_result.get("pareto_ranking", [])
        if len(pareto) > 3:
            low_impact = [p for p in pareto if abs(p["sensitivity"]) < 0.05]
            if len(low_impact) > len(pareto) * 0.5:
                flags.append({
                    "bias": "complexity_bias",
                    "evidence": f"{len(low_impact)}/{len(pareto)} parameters have sensitivity < 0.05 -- model may be over-parameterized",
                    "severity": "medium",
                    "recommendation": "Consider removing or fixing low-impact parameters",
                })

    # Check for externalization bias
    has_externalization_term = any(
        "external" in s.name.lower() or "waste" in s.name.lower()
        or "pollution" in s.name.lower() or "degradation" in s.name.lower()
        for s in specs
    )
    if not has_externalization_term and len(specs) > 3:
        flags.append({
            "bias": "externalization_bias",
            "evidence": "No parameter explicitly accounts for externalized costs, waste, or degradation",
            "severity": "high",
            "recommendation": "Add terms for costs borne outside the model boundary",
        })

    # Check for linearity bias
    linear_assumptions = [
        a for a in assumptions
        if "constant" in a.description.lower() or "linear" in a.description.lower()
    ]
    if linear_assumptions:
        flags.append({
            "bias": "linearity_bias",
            "evidence": f"Assumptions imply linearity: {[a.name for a in linear_assumptions]}",
            "severity": "medium",
            "recommendation": "Test with nonlinear or time-varying formulations",
        })

    # Sort by severity
    severity_order = {"high": 0, "medium": 1, "low": 2}
    flags.sort(key=lambda f: severity_order.get(f.get("severity", "low"), 3))

    return flags


# =========================================================================
# Formulation Comparison
# =========================================================================

def compare_formulations(
    formulations: Dict[str, Callable],
    base_params: Dict[str, float],
    param_ranges: Dict[str, Tuple[float, float]],
    output_key: Optional[str] = None,
    n_monte_carlo: int = 500,
    lower_spec: Optional[float] = None,
    upper_spec: Optional[float] = None,
    seed: int = 42,
) -> Dict[str, Any]:
    """Run the same audit on multiple alternative formulations and compare."""
    results = {}

    for name, func in formulations.items():
        sens = sensitivity_analysis(
            func, base_params, param_ranges,
            output_key=output_key, n_steps=10,
        )

        mc = monte_carlo_capability(
            func, param_ranges,
            n_samples=n_monte_carlo,
            output_key=output_key,
            lower_spec=lower_spec,
            upper_spec=upper_spec,
            seed=seed,
        )

        results[name] = {
            "baseline_output": sens["baseline_output"],
            "dominant_parameter": sens["dominant_parameter"],
            "pareto": sens["pareto_ranking"],
            "mc_mean": mc.get("mean"),
            "mc_std": mc.get("std"),
            "mc_range": mc.get("range"),
            "Cpk": mc.get("Cpk"),
            "failure_rate": mc.get("failure_rate"),
        }

    # Divergence analysis
    baselines = {n: r["baseline_output"] for n, r in results.items()}
    means = {n: r["mc_mean"] for n, r in results.items() if r["mc_mean"] is not None}

    if len(means) > 1:
        mean_vals = list(means.values())
        spread = max(mean_vals) - min(mean_vals)
        avg = sum(mean_vals) / len(mean_vals)
        divergence_ratio = spread / abs(avg) if avg != 0 else float("inf")
    else:
        divergence_ratio = 0

    dominant_params = {n: r["dominant_parameter"] for n, r in results.items()}
    dominant_agreement = len(set(dominant_params.values())) == 1

    return {
        "formulations": results,
        "divergence": {
            "baseline_outputs": baselines,
            "mc_means": means,
            "divergence_ratio": round(divergence_ratio, 4),
            "dominant_parameters": dominant_params,
            "dominant_agreement": dominant_agreement,
        },
        "recommendation": (
            "Formulations agree -- choice has low impact"
            if divergence_ratio < 0.1 and dominant_agreement
            else "Formulations diverge -- design choice significantly affects results"
        ),
    }
