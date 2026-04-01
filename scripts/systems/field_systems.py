#!/usr/bin/env python3
"""
field_systems.py — Portable rule-field engine for regenerative system tracking.

Purpose
-------
Models agricultural and ecological systems through a constraint-based framework
grounded in thermodynamics and systems dynamics.  Tracks regeneration capacity,
effective yield (accounting for waste and nutrient density), ecological coupling
amplification, and valuation distortion between market price and true
thermodynamic cost.

Core concepts
-------------
- **Constraint layer**: non-negotiable biophysical rules (soil trend, water
  retention, energy ratio, nutrient adequacy, extraction limits).
- **Effective yield**: true nourishment throughput after waste and nutrient-
  density adjustments, including compensatory-consumption demand.
- **Ecological coupling**: amplification of effective production by surrounding
  ecological support area (g(k) = 1 + alpha * k).
- **Valuation distortion**: gap between discounted market value (which ignores
  externalities) and discounted true value (which includes external and
  irreversibility costs).

References
----------
- Odum, H.T. (1996). *Environmental Accounting: Emergy and Environmental
  Decision Making*. Wiley.
- Prigogine, I. & Stengers, I. (1984). *Order Out of Chaos*. Bantam.
- Altieri, M.A. (1995). *Agroecology: The Science of Sustainable Agriculture*.
  Westview Press.
- Costanza, R. et al. (1997). "The value of the world's ecosystem services
  and natural capital." *Nature*, 387, 253-260.

Usage
-----
    python3 scripts/field_systems.py --help
    python3 scripts/field_systems.py                          # default state
    python3 scripts/field_systems.py --soil-trend -0.1        # degrading soil
    python3 scripts/field_systems.py --json                   # JSON output
    python3 scripts/field_systems.py --ecological 50 30 0.7   # coupling report
    python3 scripts/field_systems.py --valuation 100 20 40 10 # distortion report
"""

from typing import Dict, Any, Optional
import argparse
import json
import math
import sys

# ------------------
# Defaults
# ------------------

DEFAULTS = {
    "soil_trend": 0.0,
    "water_retention": 0.5,
    "input_energy": 1.0,
    "output_yield": 1.0,
    "disturbance": 0.0,
    "waste_factor": 0.3,
    "nutrient_density": 0.8,
}

BASELINES = {
    "water_retention_min": 0.4,
    "energy_ratio_min": 1.0,
    "nutrient_density_min": 0.7,
}

# ------------------
# State Helpers
# ------------------


def fill_state(state: Dict[str, Any]) -> Dict[str, float]:
    """Fill missing values with defaults."""
    return {k: float(state.get(k, DEFAULTS[k])) for k in DEFAULTS}


def regen_capacity(state: Dict[str, float]) -> float:
    """
    Regeneration capacity proxy.
    Scales with soil health and water retention, penalized by disturbance.
    """
    base = 1.0
    soil_factor = 1.0 + state["soil_trend"]
    water_factor = state["water_retention"]
    disturbance_penalty = 1.0 - state["disturbance"]
    return base * soil_factor * water_factor * disturbance_penalty


# ------------------
# Constraint Layer
# ------------------


def constraints(state: Dict[str, float]) -> Dict[str, bool]:
    """Non-negotiable system rules."""
    rc = regen_capacity(state)
    energy_ratio = (
        state["output_yield"] / state["input_energy"]
        if state["input_energy"] > 0 else 0
    )
    return {
        "soil_positive": state["soil_trend"] >= 0,
        "water_non_degrading": state["water_retention"] >= BASELINES["water_retention_min"],
        "no_overextraction": state["output_yield"] <= rc,
        "energy_ratio": energy_ratio >= BASELINES["energy_ratio_min"],
        "nutrient_adequate": state["nutrient_density"] >= BASELINES["nutrient_density_min"],
    }


def drift(state: Dict[str, float]) -> Dict[str, bool]:
    """Which constraints are violated."""
    c = constraints(state)
    return {k: not v for k, v in c.items()}


# ------------------
# Suggestions
# ------------------


def suggest(state: Dict[str, float]) -> Dict[str, Any]:
    """Structured suggestions based on drift."""
    issues = drift(state)
    actions = []
    if issues.get("soil_positive"):
        actions.append("Increase biomass input, reduce tillage/disturbance")
    if issues.get("water_non_degrading"):
        actions.append("Improve water retention (mulch, contouring, infiltration)")
    if issues.get("no_overextraction"):
        actions.append("Reduce yield pressure or increase regeneration capacity")
    if issues.get("energy_ratio"):
        actions.append("Reduce external inputs or improve system efficiency")
    if issues.get("nutrient_adequate"):
        actions.append("Increase soil biology, reduce monoculture pressure")
    return {"issues": issues, "actions": actions}


# ------------------
# Scoring
# ------------------


def score(state: Dict[str, float]) -> float:
    """Fraction of constraints satisfied (0-1)."""
    c = constraints(state)
    return sum(c.values()) / len(c)


# ------------------
# Effective Yield Accounting
# ------------------


def effective_yield(state: Dict[str, float]) -> Dict[str, float]:
    """
    True nourishment throughput accounting for waste and nutrient density.

    Y_usable   = Y_gross * (1 - W_f)
    Y_nutrient = Y_usable * N_d
    Y_behavioral = Y_nutrient / N_d  (compensatory consumption)

    The behavioral demand equation:
        Y_required = Y_target / ((1 - W_f) * N_d**2)
    """
    wf = state.get("waste_factor", DEFAULTS["waste_factor"])
    nd = state.get("nutrient_density", DEFAULTS["nutrient_density"])
    yg = state["output_yield"]

    usable = yg * (1 - wf)
    nutrient = usable * nd
    # Compensatory: low density -> eat more to meet needs
    behavioral = nutrient / nd if nd > 0 else 0

    # Amplification factor: how much extra production the system
    # must generate to actually nourish (vs raw yield)
    amplification = 1.0 / ((1 - wf) * nd * nd) if (wf < 1 and nd > 0) else float('inf')

    return {
        "gross": yg,
        "usable": usable,
        "nutrient_adjusted": nutrient,
        "behavioral_demand": behavioral,
        "amplification_factor": amplification,
    }


# ------------------
# Ecological Coupling
# ------------------


def ecological_amplification(
    production_area: float,
    ecological_area: float,
    coupling_strength: float,
    max_amplification: float = 2.0,
) -> Dict[str, float]:
    """
    Model: effective yield = Y_adj * g(k)
    where g(k) = 1 + alpha * k

    Parameters
    ----------
    production_area : float
        Acres under cultivation.
    ecological_area : float
        Acres of ecological support.
    coupling_strength : float
        k, 0-1.
    max_amplification : float
        alpha, maximum ecological multiplier.

    Returns
    -------
    dict with g(k), effective area ratio, and notes.
    """
    g = 1.0 + max_amplification * coupling_strength
    effective_production = production_area * g
    total_area = production_area + ecological_area

    return {
        "production_area": production_area,
        "ecological_area": ecological_area,
        "coupling_strength": coupling_strength,
        "amplification_g": g,
        "effective_production_equivalent": effective_production,
        "total_area": total_area,
        "land_efficiency": effective_production / total_area if total_area > 0 else 0,
    }


# ------------------
# Valuation Distortion
# ------------------


def valuation_distortion(
    extractive_value: float,
    internal_cost: float,
    external_cost: float,
    irreversibility_cost: float,
    discount_rate: float = 0.05,
    horizon_years: int = 30,
) -> Dict[str, float]:
    """
    Market price vs thermodynamic reality.

    P_market uses: (V_e - C_internal) / (1+r)^t
    P_true uses:   (V_e - C_internal - C_external - C_irreversibility) / (1+r)^t

    Returns ratio and gap.
    """
    p_market = sum(
        (extractive_value - internal_cost) / ((1 + discount_rate) ** t)
        for t in range(horizon_years)
    )
    p_true = sum(
        (extractive_value - internal_cost - external_cost - irreversibility_cost)
        / ((1 + discount_rate) ** t)
        for t in range(horizon_years)
    )

    return {
        "market_value": max(0, p_market),
        "true_value": p_true,
        "distortion_ratio": p_market / p_true if p_true != 0 else float('inf'),
        "hidden_subsidy": max(0, p_market - p_true) if p_true < p_market else 0,
        "discount_rate": discount_rate,
        "horizon_years": horizon_years,
    }


# ------------------
# Full Report
# ------------------


def report(state: Dict[str, Any]) -> Dict[str, Any]:
    """Full evaluation pipeline."""
    s = fill_state(state)
    return {
        "state": s,
        "constraints": constraints(s),
        "drift": drift(s),
        "score": score(s),
        "suggestions": suggest(s),
        "effective_yield": effective_yield(s),
        "regen_capacity": regen_capacity(s),
    }


# ------------------
# CLI
# ------------------


def _format_section(title: str, data: Any, indent: int = 0) -> str:
    """Pretty-print a dict or value with a section header."""
    prefix = "  " * indent
    lines = [f"{prefix}{title}"]
    if isinstance(data, dict):
        for k, v in data.items():
            if isinstance(v, dict):
                lines.append(_format_section(k, v, indent + 1))
            elif isinstance(v, list):
                lines.append(f"{prefix}  {k}:")
                for item in v:
                    lines.append(f"{prefix}    - {item}")
            elif isinstance(v, float):
                lines.append(f"{prefix}  {k}: {v:.4f}")
            else:
                lines.append(f"{prefix}  {k}: {v}")
    elif isinstance(data, float):
        lines.append(f"{prefix}  {data:.4f}")
    else:
        lines.append(f"{prefix}  {data}")
    return "\n".join(lines)


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Regenerative field-systems engine: constraint checking, "
                    "effective yield, ecological coupling, and valuation distortion.",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
examples:
  %(prog)s                              # report with default state
  %(prog)s --soil-trend -0.1            # degrading soil
  %(prog)s --disturbance 0.4 --json     # JSON output
  %(prog)s --ecological 50 30 0.7       # ecological coupling analysis
  %(prog)s --valuation 100 20 40 10     # valuation distortion analysis
        """,
    )

    # State parameters
    state_group = parser.add_argument_group("field state parameters")
    state_group.add_argument(
        "--soil-trend", type=float, default=DEFAULTS["soil_trend"],
        help="soil health trend; >=0 is positive (default: %(default)s)",
    )
    state_group.add_argument(
        "--water-retention", type=float, default=DEFAULTS["water_retention"],
        help="water retention factor 0-1 (default: %(default)s)",
    )
    state_group.add_argument(
        "--input-energy", type=float, default=DEFAULTS["input_energy"],
        help="external energy input (default: %(default)s)",
    )
    state_group.add_argument(
        "--output-yield", type=float, default=DEFAULTS["output_yield"],
        help="gross yield (default: %(default)s)",
    )
    state_group.add_argument(
        "--disturbance", type=float, default=DEFAULTS["disturbance"],
        help="disturbance level 0-1 (default: %(default)s)",
    )
    state_group.add_argument(
        "--waste-factor", type=float, default=DEFAULTS["waste_factor"],
        help="fraction of yield wasted 0-1 (default: %(default)s)",
    )
    state_group.add_argument(
        "--nutrient-density", type=float, default=DEFAULTS["nutrient_density"],
        help="nutrient density factor 0-1 (default: %(default)s)",
    )

    # Sub-analyses
    sub_group = parser.add_argument_group("sub-analyses")
    sub_group.add_argument(
        "--ecological", nargs=3, type=float,
        metavar=("PROD_AREA", "ECO_AREA", "COUPLING"),
        help="run ecological coupling analysis (production_area ecological_area coupling_strength)",
    )
    sub_group.add_argument(
        "--valuation", nargs=4, type=float,
        metavar=("EXTRACT_V", "INT_COST", "EXT_COST", "IRREVERSIBILITY"),
        help="run valuation distortion analysis",
    )
    sub_group.add_argument(
        "--discount-rate", type=float, default=0.05,
        help="discount rate for valuation (default: %(default)s)",
    )
    sub_group.add_argument(
        "--horizon", type=int, default=30,
        help="horizon in years for valuation (default: %(default)s)",
    )

    # Output
    parser.add_argument(
        "--json", action="store_true", dest="json_output",
        help="output as JSON",
    )

    args = parser.parse_args()

    # Build state from CLI args
    state = {
        "soil_trend": args.soil_trend,
        "water_retention": args.water_retention,
        "input_energy": args.input_energy,
        "output_yield": args.output_yield,
        "disturbance": args.disturbance,
        "waste_factor": args.waste_factor,
        "nutrient_density": args.nutrient_density,
    }

    results = {}

    # Core report
    results["report"] = report(state)

    # Optional ecological coupling
    if args.ecological:
        prod, eco, coupling = args.ecological
        results["ecological_coupling"] = ecological_amplification(prod, eco, coupling)

    # Optional valuation distortion
    if args.valuation:
        ev, ic, ec, irr = args.valuation
        results["valuation_distortion"] = valuation_distortion(
            ev, ic, ec, irr,
            discount_rate=args.discount_rate,
            horizon_years=args.horizon,
        )

    # Output
    if args.json_output:
        print(json.dumps(results, indent=2, default=str))
    else:
        # Pretty print
        rpt = results["report"]
        print("=" * 60)
        print("  FIELD SYSTEMS — Regenerative Constraint Report")
        print("=" * 60)
        print()
        print(_format_section("State:", rpt["state"]))
        print()
        print(_format_section("Constraints:", rpt["constraints"]))
        print()
        print(_format_section("Drift (violations):", rpt["drift"]))
        print()
        print(f"Score: {rpt['score']:.2f}  ({sum(rpt['constraints'].values())}"
              f"/{len(rpt['constraints'])} constraints satisfied)")
        print(f"Regeneration capacity: {rpt['regen_capacity']:.4f}")
        print()
        print(_format_section("Effective Yield:", rpt["effective_yield"]))
        print()
        suggestions = rpt["suggestions"]
        if suggestions["actions"]:
            print("Suggestions:")
            for a in suggestions["actions"]:
                print(f"  - {a}")
        else:
            print("All constraints satisfied — no corrective actions needed.")

        if "ecological_coupling" in results:
            print()
            print("-" * 60)
            print(_format_section("Ecological Coupling:", results["ecological_coupling"]))

        if "valuation_distortion" in results:
            print()
            print("-" * 60)
            print(_format_section("Valuation Distortion:", results["valuation_distortion"]))

        print()


if __name__ == "__main__":
    main()
