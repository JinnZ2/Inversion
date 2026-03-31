#!/usr/bin/env python3
"""
First Principles Audit — Assumption and Design Choice Validation

Provides a framework for auditing computational models against first
principles. Each assumption is checked for falsifiability, each design
choice is assessed for bias risk, and the overall model is stress-tested
by perturbing parameters across their valid ranges.

Core structures:
  - AssumptionRecord: tracks a model assumption with its basis,
    falsification test, and impact assessment
  - DesignChoice: tracks a methodology choice with alternatives
    considered and bias risks identified
  - full_audit(): runs parameter perturbation, assumption validation,
    and design choice assessment on a target function

This module is consumed by study_extractor.py to audit auto-generated
code from study/white paper extraction pipelines.

References:
  - Popper (1959): falsifiability as demarcation criterion
  - Saltelli et al. (2004): sensitivity analysis in practice
  - Ioannidis (2005): why most published research findings are false
"""

from __future__ import annotations

import argparse
import json
import math
import sys
from dataclasses import dataclass, field, asdict
from typing import Any, Callable, Dict, List, Optional, Tuple


# ---------------------------------------------------------------------------
# Data structures
# ---------------------------------------------------------------------------

@dataclass
class AssumptionRecord:
    """A model assumption with falsifiability tracking."""
    name: str
    description: str
    basis: str  # "physics", "empirical", "convention", "simplification"
    falsifiable: bool
    falsification_test: str
    impact_if_wrong: str
    validated: Optional[bool] = None
    validation_notes: str = ""

    def assess(self) -> Dict[str, Any]:
        """Assess assumption quality."""
        issues = []
        if not self.falsifiable:
            issues.append("Not falsifiable — cannot be empirically tested")
        if self.basis == "convention":
            issues.append("Based on convention rather than physics/empirical evidence")
        if self.basis == "simplification":
            issues.append("Simplification — may not hold under all conditions")
        if not self.falsification_test:
            issues.append("No falsification test defined")
        return {
            "name": self.name,
            "basis": self.basis,
            "falsifiable": self.falsifiable,
            "issues": issues,
            "risk_level": "HIGH" if len(issues) >= 2 else "MODERATE" if issues else "LOW",
        }


@dataclass
class DesignChoice:
    """A methodology/design choice with alternatives and bias assessment."""
    name: str
    chosen: str
    alternatives: List[str]
    reason: str
    bias_risk: List[str]  # e.g., ["optimization_bias", "scale_bias"]
    who_decided: str

    def assess(self) -> Dict[str, Any]:
        """Assess design choice quality."""
        issues = []
        if not self.alternatives:
            issues.append("No alternatives considered")
        if not self.bias_risk:
            issues.append("No bias risks identified")
        if len(self.alternatives) < 2:
            issues.append("Fewer than 2 alternatives — limited exploration")
        return {
            "name": self.name,
            "chosen": self.chosen,
            "n_alternatives": len(self.alternatives),
            "bias_risks": self.bias_risk,
            "issues": issues,
            "risk_level": "HIGH" if len(issues) >= 2 else "MODERATE" if issues else "LOW",
        }


# ---------------------------------------------------------------------------
# Parameter perturbation
# ---------------------------------------------------------------------------

def perturb_parameters(
    base_params: Dict[str, float],
    param_ranges: Dict[str, Tuple[float, float]],
    n_samples: int = 20,
) -> List[Dict[str, float]]:
    """Generate parameter perturbations for sensitivity analysis.

    Sweeps each parameter across its range while holding others at baseline.
    Returns a list of parameter dicts to evaluate.
    """
    perturbations = [dict(base_params)]  # include baseline

    for param_name, (lo, hi) in param_ranges.items():
        if param_name not in base_params:
            continue
        for i in range(n_samples):
            frac = i / max(n_samples - 1, 1)
            value = lo + frac * (hi - lo)
            perturbed = dict(base_params)
            perturbed[param_name] = value
            perturbations.append(perturbed)

    return perturbations


def sensitivity_analysis(
    func: Callable,
    base_params: Dict[str, float],
    param_ranges: Dict[str, Tuple[float, float]],
    output_key: str = "score",
    n_samples: int = 20,
) -> Dict[str, Any]:
    """Run one-at-a-time sensitivity analysis on a function.

    Returns per-parameter sensitivity (output range when that param is swept).
    """
    baseline_result = func(base_params)
    if isinstance(baseline_result, dict):
        baseline_value = baseline_result.get(output_key, 0.0)
    else:
        baseline_value = float(baseline_result)

    sensitivities = {}
    for param_name, (lo, hi) in param_ranges.items():
        if param_name not in base_params:
            continue
        values = []
        for i in range(n_samples):
            frac = i / max(n_samples - 1, 1)
            test_val = lo + frac * (hi - lo)
            perturbed = dict(base_params)
            perturbed[param_name] = test_val
            result = func(perturbed)
            if isinstance(result, dict):
                values.append(result.get(output_key, 0.0))
            else:
                values.append(float(result))

        output_range = max(values) - min(values) if values else 0.0
        sensitivities[param_name] = {
            "output_range": round(output_range, 4),
            "min_output": round(min(values), 4) if values else 0.0,
            "max_output": round(max(values), 4) if values else 0.0,
            "baseline": round(baseline_value, 4),
        }

    # Rank by sensitivity
    ranked = sorted(sensitivities.items(), key=lambda x: -x[1]["output_range"])
    return {
        "baseline_value": round(baseline_value, 4),
        "sensitivities": dict(ranked),
        "most_sensitive": ranked[0][0] if ranked else None,
        "least_sensitive": ranked[-1][0] if ranked else None,
    }


# ---------------------------------------------------------------------------
# Full audit
# ---------------------------------------------------------------------------

def full_audit(
    func: Callable,
    base_params: Dict[str, float],
    param_ranges: Dict[str, Tuple[float, float]],
    assumptions: Optional[List[AssumptionRecord]] = None,
    design_choices: Optional[List[DesignChoice]] = None,
    output_key: str = "score",
    n_samples: int = 20,
) -> Dict[str, Any]:
    """Run a complete first-principles audit.

    Combines sensitivity analysis, assumption assessment, and design
    choice evaluation into a single diagnostic report.
    """
    # Sensitivity analysis
    sa = sensitivity_analysis(func, base_params, param_ranges, output_key, n_samples)

    # Assumption assessment
    assumption_results = []
    if assumptions:
        for a in assumptions:
            assumption_results.append(a.assess())
    high_risk_assumptions = sum(1 for r in assumption_results if r["risk_level"] == "HIGH")

    # Design choice assessment
    choice_results = []
    if design_choices:
        for dc in design_choices:
            choice_results.append(dc.assess())
    high_risk_choices = sum(1 for r in choice_results if r["risk_level"] == "HIGH")

    # Overall audit score
    total_issues = high_risk_assumptions + high_risk_choices
    if total_issues == 0:
        audit_level = "CLEAN"
    elif total_issues <= 2:
        audit_level = "MINOR CONCERNS"
    elif total_issues <= 5:
        audit_level = "SIGNIFICANT CONCERNS"
    else:
        audit_level = "CRITICAL — REVIEW REQUIRED"

    return {
        "sensitivity": sa,
        "assumptions": assumption_results,
        "design_choices": choice_results,
        "summary": {
            "total_assumptions": len(assumption_results),
            "high_risk_assumptions": high_risk_assumptions,
            "total_design_choices": len(choice_results),
            "high_risk_choices": high_risk_choices,
            "most_sensitive_param": sa.get("most_sensitive"),
            "audit_level": audit_level,
        },
    }


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------

def main() -> None:
    parser = argparse.ArgumentParser(
        description=(
            "First principles audit framework. Run sensitivity analysis, "
            "assumption validation, and design choice assessment on "
            "computational models. Use --demo for an example audit."
        ),
    )
    parser.add_argument(
        "--demo", action="store_true",
        help="Run a demonstration audit on a simple model",
    )
    parser.add_argument(
        "--json", action="store_true",
        help="Output as JSON",
    )
    args = parser.parse_args()

    if args.demo:
        # Demo: audit a simple quadratic model
        def demo_model(params):
            x = params.get("x", 1.0)
            k = params.get("k", 1.0)
            noise = params.get("noise", 0.0)
            return {"score": k * x ** 2 + noise, "x": x}

        base = {"x": 1.0, "k": 2.0, "noise": 0.0}
        ranges = {"x": (0.0, 5.0), "k": (0.1, 10.0), "noise": (-1.0, 1.0)}

        assumptions = [
            AssumptionRecord(
                name="Quadratic relationship",
                description="Output scales as x^2",
                basis="simplification",
                falsifiable=True,
                falsification_test="Compare to empirical data across x range",
                impact_if_wrong="Model predictions diverge at extreme x values",
            ),
            AssumptionRecord(
                name="Additive noise",
                description="Noise is additive and independent",
                basis="convention",
                falsifiable=True,
                falsification_test="Check residual autocorrelation",
                impact_if_wrong="Confidence intervals invalid",
            ),
        ]

        design_choices = [
            DesignChoice(
                name="Model form",
                chosen="Quadratic polynomial",
                alternatives=["Exponential", "Power law", "Neural network"],
                reason="Simplest model that captures observed curvature",
                bias_risk=["simplification_bias", "linearity_bias"],
                who_decided="Analyst",
            ),
        ]

        result = full_audit(
            func=demo_model,
            base_params=base,
            param_ranges=ranges,
            assumptions=assumptions,
            design_choices=design_choices,
        )

        if args.json:
            print(json.dumps(result, indent=2))
        else:
            print("=" * 70)
            print("  FIRST PRINCIPLES AUDIT — Demo")
            print("=" * 70)
            s = result["summary"]
            print(f"\n  Audit Level: {s['audit_level']}")
            print(f"  Most Sensitive Parameter: {s['most_sensitive_param']}")
            print(f"  Assumptions: {s['total_assumptions']} ({s['high_risk_assumptions']} high risk)")
            print(f"  Design Choices: {s['total_design_choices']} ({s['high_risk_choices']} high risk)")

            print("\n  Sensitivity Analysis:")
            for param, data in result["sensitivity"]["sensitivities"].items():
                print(f"    {param:>10}: range={data['output_range']:.4f}  [{data['min_output']:.4f} .. {data['max_output']:.4f}]")

            print("\n  Assumption Assessment:")
            for a in result["assumptions"]:
                print(f"    {a['name']}: {a['risk_level']} — {', '.join(a['issues']) if a['issues'] else 'OK'}")

            print("\n  Design Choice Assessment:")
            for dc in result["design_choices"]:
                print(f"    {dc['name']}: {dc['risk_level']} — chose '{dc['chosen']}' over {dc['n_alternatives']} alternatives")
            print()
    else:
        parser.print_help()


if __name__ == "__main__":
    main()
