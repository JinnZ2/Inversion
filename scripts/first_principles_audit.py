#!/usr/bin/env python3
"""
First Principles Audit -- Six Sigma DMAIC Validation Engine

Complete audit framework for computational models using DMAIC methodology:
  Define   -- parameter documentation and assumption tracking
  Measure  -- function introspection and parameter cataloging
  Analyze  -- one-at-a-time sensitivity analysis with Pareto ranking
  Improve  -- boundary testing and Failure Mode Effects Analysis (FMEA)
  Control  -- process capability indices (Cp, Cpk) via Monte Carlo

Layer 2 adds bias detection and design choice accountability:
  - 8 known bias patterns (optimization, recency, complexity, etc.)
  - Design choice tracking with alternative comparison
  - Formulation comparison engine

Output formats: JSON, Markdown, CSV.

Usage:
  from scripts.audit_core import audit_function, ParameterSpec, AssumptionRecord
  from scripts.bias_detection import flag_biases, DesignChoice
  from scripts.first_principles_audit import full_audit

  report = full_audit(func, params, ranges, specs=specs, assumptions=assumptions)

References:
  - Popper (1959): falsifiability as demarcation criterion
  - Saltelli et al. (2004): sensitivity analysis in practice
  - Ioannidis (2005): why most published research findings are false
  - Montgomery (2009): statistical quality control (Cp, Cpk)
  - Stamatis (2003): Failure Mode and Effect Analysis
"""

from __future__ import annotations

import argparse
import json
import os
import sys
from typing import Any, Callable, Dict, List, Optional, Tuple

# Allow running as script or module
if __name__ == "__main__":
    sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from scripts.audit_core import (
    AssumptionRecord,
    ParameterSpec,
    audit_function,
    generate_report,
    sensitivity_analysis,
)
from scripts.bias_detection import (
    DesignChoice,
    compare_formulations,
    flag_biases,
)


# =========================================================================
# Extended Audit (Layer 1 + Layer 2)
# =========================================================================

def full_audit(
    func: Callable,
    base_params: Dict[str, float],
    param_ranges: Dict[str, Tuple[float, float]],
    specs: Optional[Dict[str, ParameterSpec]] = None,
    assumptions: Optional[List[AssumptionRecord]] = None,
    design_choices: Optional[List[DesignChoice]] = None,
    alternative_formulations: Optional[Dict[str, Callable]] = None,
    output_key: Optional[str] = None,
    lower_spec: Optional[float] = None,
    upper_spec: Optional[float] = None,
    n_sensitivity_steps: int = 10,
    n_monte_carlo: int = 1000,
) -> Dict[str, Any]:
    """Complete audit: Layer 1 (mechanics) + Layer 2 (bias/design choices)."""
    # Layer 1
    layer1 = audit_function(
        func, base_params, param_ranges,
        specs=specs, assumptions=assumptions,
        output_key=output_key,
        lower_spec=lower_spec, upper_spec=upper_spec,
        n_sensitivity_steps=n_sensitivity_steps,
        n_monte_carlo=n_monte_carlo,
    )

    # Layer 2: Bias flags
    bias_flags = flag_biases(
        list(specs.values()) if specs else [],
        assumptions or [],
        design_choices or [],
        sensitivity_result={"pareto_ranking": layer1["analyze"]["pareto_ranking"]},
    )

    # Layer 2: Formulation comparison
    formulation_comparison = None
    if alternative_formulations:
        all_formulations = {"primary": func}
        all_formulations.update(alternative_formulations)
        formulation_comparison = compare_formulations(
            all_formulations, base_params, param_ranges,
            output_key=output_key,
            n_monte_carlo=n_monte_carlo,
            lower_spec=lower_spec, upper_spec=upper_spec,
        )

    # Layer 2: Design choice documentation
    design_doc = []
    if design_choices:
        for dc in design_choices:
            design_doc.append({
                "name": dc.name,
                "chosen": dc.chosen,
                "alternatives": dc.alternatives,
                "reason": dc.reason,
                "bias_risk": dc.bias_risk,
                "who_decided": dc.who_decided,
                "alternatives_tested": (
                    formulation_comparison is not None
                    and any(
                        alt in (alternative_formulations or {})
                        for alt in dc.alternatives
                    )
                ),
            })

    # Combine
    layer1["bias_detection"] = {
        "flags": bias_flags,
        "high_severity_count": len([f for f in bias_flags if f.get("severity") == "high"]),
        "design_choices": design_doc,
        "formulation_comparison": formulation_comparison,
    }

    # Update grade to account for bias
    high_bias = len([f for f in bias_flags if f.get("severity") == "high"])
    if high_bias >= 3:
        layer1["summary"]["bias_grade"] = "FAIL -- Multiple high-severity biases detected"
    elif high_bias >= 1:
        layer1["summary"]["bias_grade"] = "WARNING -- High-severity bias detected"
    elif bias_flags:
        layer1["summary"]["bias_grade"] = "CAUTION -- Medium-severity biases present"
    else:
        layer1["summary"]["bias_grade"] = "PASS -- No significant biases detected"

    return layer1


# =========================================================================
# CLI
# =========================================================================

def main() -> None:
    parser = argparse.ArgumentParser(
        description=(
            "First Principles Audit -- Six Sigma DMAIC validation engine. "
            "Run --demo for a demonstration audit on a simple model."
        ),
    )
    parser.add_argument(
        "--demo", action="store_true",
        help="Run a demonstration audit on a quadratic model",
    )
    parser.add_argument(
        "--json", action="store_true",
        help="Output as JSON",
    )
    parser.add_argument(
        "--markdown", action="store_true",
        help="Output as Markdown report",
    )
    parser.add_argument(
        "--csv", action="store_true",
        help="Output as CSV",
    )
    args = parser.parse_args()

    if args.demo:
        # Demo: audit a simple quadratic model
        def demo_model(x=1.0, k=2.0, noise=0.0):
            return {"score": k * x ** 2 + noise, "x": x}

        base = {"x": 1.0, "k": 2.0, "noise": 0.0}
        ranges = {"x": (0.0, 5.0), "k": (0.1, 10.0), "noise": (-1.0, 1.0)}

        specs = {
            "x": ParameterSpec(
                name="x", default_value=1.0, units="m",
                physical_meaning="Position", source="measured",
                valid_min=0.0, valid_max=10.0, uncertainty=0.1,
            ),
            "k": ParameterSpec(
                name="k", default_value=2.0, units="N/m",
                physical_meaning="Spring constant", source="literature",
                valid_min=0.01, valid_max=100.0,
            ),
            "noise": ParameterSpec(
                name="noise", default_value=0.0, units="N",
                physical_meaning="Measurement noise", source="assumed",
            ),
        }

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
            specs=specs,
            assumptions=assumptions,
            design_choices=design_choices,
            output_key="score",
            lower_spec=-5.0,
            upper_spec=60.0,
            n_monte_carlo=500,
        )

        if args.json:
            print(json.dumps(result, indent=2, default=str))
        elif args.markdown:
            print(generate_report(result, fmt="markdown"))
        elif args.csv:
            print(generate_report(result, fmt="csv"))
        else:
            # Human-readable summary
            s = result["summary"]
            print("=" * 70)
            print("  FIRST PRINCIPLES AUDIT -- Demo (Quadratic Model)")
            print("=" * 70)
            print(f"\n  Overall Grade:     {s['overall_grade']}")
            print(f"  Bias Grade:        {result['summary'].get('bias_grade', 'N/A')}")
            print(f"  Most Sensitive:    {s['dominant_parameter']}")
            print(f"  Documentation:     {s['documentation_ratio']:.0%}")
            print(f"  Boundary Failures: {s['boundary_failure_rate']:.0%}")
            print(f"  MC Failure Rate:   {s['monte_carlo_failure_rate']:.1%}")
            if s.get("Cpk") is not None:
                print(f"  Cpk:               {s['Cpk']:.3f}")

            print("\n  Sensitivity Ranking:")
            for item in result["analyze"]["pareto_ranking"]:
                print(f"    {item['rank']}. {item['parameter']:>10}: {item['sensitivity']:.4f}")

            print("\n  FMEA (Top 3 by RPN):")
            for item in result["improve"]["fmea"][:3]:
                print(f"    {item['item']:>20}: RPN={item['rpn']} ({item['type']})")

            bd = result.get("bias_detection", {})
            if bd.get("flags"):
                print(f"\n  Bias Flags ({len(bd['flags'])}):")
                for flag in bd["flags"][:5]:
                    print(f"    [{flag['severity'].upper():>6}] {flag['bias']}: {flag['evidence'][:60]}")

            print()
    else:
        parser.print_help()


if __name__ == "__main__":
    main()
