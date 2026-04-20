#!/usr/bin/env python3
"""
metabolic_accounting.py -- Thermodynamic accounting primitives for the
Inversion corpus.

Vendored and consolidated from:
    https://github.com/JinnZ2/metabolic-accounting  (CC0)

Upstream module map:

    basin_states/base.py          -> BasinState
    thermodynamics/exergy.py      -> ExergyFlow, XduConverter,
                                     ThermodynamicViolation,
                                     check_nonnegative_destruction,
                                     check_regen_floor, check_closure
    accounting/glucose.py         -> (simplified here as MetabolicFlow)
    verdict/assess.py             -> Verdict, basin_trajectory_verdict,
                                     min_time_to_red, yield_signal, assess

The upstream framework is a full firm-level metabolic accounting system
with cascade detection, reserve hierarchies, and per-metric regeneration
registries. That depth is not needed to strengthen the Inversion corpus:
what Inversion uses is the thermodynamic scaffolding itself -- basin
states, forced regeneration drawdown, the GREEN/AMBER/RED/BLACK verdict,
and the Gouy-Stodola invariants.

This adapter keeps the vendored physical invariants verbatim, keeps
``BasinState`` verbatim, and replaces the heavy ``GlucoseFlow`` +
``compute_flow`` pipeline with a ``MetabolicFlow`` dataclass whose
numbers callers provide directly. For full firm-level accounting, use
the upstream repository instead of this file.

Canonical reference for the thermodynamic law:
    Gouy-Stodola theorem -- exergy destruction >= 0 always.
    Sciubba & Wall (2007); Sciubba (2021).
"""

from __future__ import annotations

import argparse
import json
import sys
from dataclasses import dataclass, field, asdict
from math import inf, isinf
from typing import Dict, List, Optional


# ---------------------------------------------------------------------------
# Canonical unit
# ---------------------------------------------------------------------------

UNIT = "xdu"  # exergy-destruction-equivalent
DEFAULT_T0_KELVIN = 298.15


# ---------------------------------------------------------------------------
# BasinState (vendored verbatim from basin_states/base.py)
# ---------------------------------------------------------------------------


@dataclass
class BasinState:
    """A substrate the system depends on. Has current state, capacity,
    trajectory (rate of change; positive = regenerating, negative =
    depleting), and cliff thresholds below which cascade failure is
    triggered.

    For the Inversion corpus, basins are typically abstract -- a
    "human-rights-reporting basin," an "AI-training-corpus basin," a
    "biological-integrity basin" -- but the arithmetic is the same as
    in the upstream physical-substrate use case.
    """

    name: str
    basin_type: str = ""
    state: Dict[str, float] = field(default_factory=dict)
    capacity: Dict[str, float] = field(default_factory=dict)
    trajectory: Dict[str, float] = field(default_factory=dict)
    cliff_thresholds: Dict[str, float] = field(default_factory=dict)
    high_is_bad: set = field(default_factory=set)
    last_updated: Optional[str] = None
    notes: str = ""

    def fraction_remaining(self, key: str) -> float:
        cap = self.capacity.get(key)
        if cap is None or cap == 0:
            return float("nan")
        return self.state.get(key, 0.0) / cap

    def time_to_cliff(self, key: str) -> Optional[float]:
        s = self.state.get(key)
        t = self.trajectory.get(key)
        c = self.cliff_thresholds.get(key)
        if s is None or t is None or c is None:
            return None
        if t >= 0:
            return None
        if s <= c:
            return 0.0
        return (s - c) / abs(t)

    def is_degrading(self) -> List[str]:
        return [k for k, v in self.trajectory.items() if v < 0]


# ---------------------------------------------------------------------------
# Thermodynamic invariants (vendored verbatim from thermodynamics/exergy.py)
# ---------------------------------------------------------------------------


class ThermodynamicViolation(Exception):
    """Raised when a computation would violate the second law."""


@dataclass
class ExergyFlow:
    """A single exergy transfer event in the ledger.

    source, sink are free-form identifiers. amount is in xdu. destroyed
    is the Gouy-Stodola loss (must be >= 0; higher = more irreversible).
    """

    source: str
    sink: str
    amount: float
    destroyed: float = 0.0
    note: str = ""


def check_nonnegative_destruction(amount: float, context: str = "") -> None:
    """Gouy-Stodola floor: any claimed exergy destruction must be >= 0."""
    if isinf(amount):
        return
    if amount < -1e-9:
        raise ThermodynamicViolation(
            f"negative exergy destruction ({amount:.6g} xdu) at {context} -- "
            "this would require entropy to decrease spontaneously, which "
            "violates the second law. The computation that produced this "
            "value has a bug."
        )


def check_regen_floor(regen_cost_xdu: float, damage_energy_xdu: float, context: str = "") -> None:
    """Directional invariant: regeneration must cost >= damage cost.

    Reversing degradation requires work against the entropy gradient.
    Ad-hoc regen scalars that return less than damage violate the second
    law even if their authors did not notice.
    """
    if isinf(regen_cost_xdu):
        return
    if damage_energy_xdu <= 0:
        return
    if regen_cost_xdu < damage_energy_xdu:
        raise ThermodynamicViolation(
            f"regeneration cost {regen_cost_xdu:.4g} xdu is less than damage "
            f"cost {damage_energy_xdu:.4g} xdu at {context} -- this would "
            "produce net-negative entropy. Regen cost functions must return "
            "values at or above the damage cost."
        )


def check_closure(
    imposed: float,
    primary: float,
    secondary: float,
    tertiary: float,
    environment: float,
    tolerance: float = 1e-6,
    context: str = "",
) -> None:
    """First-law mass balance at the reserve hierarchy.

    imposed == primary + secondary + tertiary + environment.

    Fails closed: if the balance is broken, stress was either invented
    or destroyed and the computation is wrong.
    """
    if any(isinf(x) for x in (imposed, primary, secondary, tertiary, environment)):
        return
    total = primary + secondary + tertiary + environment
    if abs(total - imposed) > tolerance:
        raise ThermodynamicViolation(
            f"closure failure at {context}: imposed={imposed:.6g} xdu, "
            f"distributed={total:.6g} xdu "
            f"(primary={primary:.4g}, secondary={secondary:.4g}, "
            f"tertiary={tertiary:.4g}, environment={environment:.4g}). "
            "Mass balance broken -- computation is wrong."
        )


@dataclass
class XduConverter:
    """Policy-layer conversion between xdu (physical) and currency.

    The conversion is a declared parameter, not a physical constant.
    Documenting it explicitly keeps the physics separate from the policy.
    """

    xdu_per_currency_unit: float = 1.0
    label: str = "1:1 placeholder"

    def to_currency(self, xdu: float) -> float:
        if self.xdu_per_currency_unit == 0:
            raise ValueError("xdu_per_currency_unit must not be zero")
        if isinf(xdu):
            return xdu
        return xdu / self.xdu_per_currency_unit

    def to_xdu(self, currency: float) -> float:
        if isinf(currency):
            return currency
        return currency * self.xdu_per_currency_unit


# ---------------------------------------------------------------------------
# MetabolicFlow (simplified from accounting/glucose.py)
# ---------------------------------------------------------------------------


@dataclass
class MetabolicFlow:
    """One period of glucose flow. Values in xdu (or currency; callers
    are responsible for consistency).

    Inputs come in as numbers rather than being derived from a cascade
    simulator. For Inversion use, the "firm" is typically an institution
    or an information ecosystem, and ``revenue`` / ``direct_operating_cost``
    are interpretive proxies (legitimacy inflow, operational overhead).

    Key semantics preserved from upstream:
      - reported_profit ignores regeneration (conventional view)
      - metabolic_profit charges the full forced drawdown
      - environment_loss is irreversible; treated as an extraordinary item
      - irreversible_metrics and infinite regeneration_required propagate
        honestly (inf is the signal, not a bug)
    """

    revenue: float = 0.0
    direct_operating_cost: float = 0.0
    regeneration_paid: float = 0.0
    regeneration_required: float = 0.0
    cascade_burn: float = 0.0
    regeneration_debt: float = 0.0
    reserve_drawdown_cost: float = 0.0
    environment_loss: float = 0.0
    cumulative_environment_loss: float = 0.0
    irreversible_metrics: List[str] = field(default_factory=list)
    notes: List[str] = field(default_factory=list)

    def has_irreversibility(self) -> bool:
        return (
            len(self.irreversible_metrics) > 0 or isinf(self.regeneration_required)
        )

    def reported_profit(self) -> float:
        return self.revenue - self.direct_operating_cost - self.cascade_burn

    def metabolic_profit(self) -> float:
        if isinf(self.regeneration_required):
            return -inf
        return (
            self.revenue
            - self.direct_operating_cost
            - self.regeneration_required
            - self.cascade_burn
            - self.reserve_drawdown_cost
        )

    def metabolic_profit_with_loss(self) -> float:
        if isinf(self.regeneration_required) or isinf(self.environment_loss):
            return -inf
        return self.metabolic_profit() - self.environment_loss

    def regeneration_gap(self) -> float:
        if isinf(self.regeneration_required):
            return inf if self.regeneration_paid < inf else 0.0
        return max(0.0, self.regeneration_required - self.regeneration_paid)

    def is_extraordinary_loss_material(
        self, revenue_threshold: float = 0.05, min_absolute: float = 0.0
    ) -> bool:
        if self.environment_loss <= 0:
            return False
        if self.environment_loss < min_absolute:
            return False
        if self.revenue <= 0:
            return self.environment_loss >= min_absolute
        return self.environment_loss >= revenue_threshold * self.revenue


# ---------------------------------------------------------------------------
# Verdict layer (simplified from verdict/assess.py)
# ---------------------------------------------------------------------------


@dataclass
class Verdict:
    sustainable_yield_signal: str
    basin_trajectory: str
    time_to_red: Optional[float]
    forced_drawdown: float
    regeneration_debt: float
    metabolic_profit: float
    reported_profit: float
    profit_gap: float
    extraordinary_item_flagged: bool = False
    extraordinary_item_amount: float = 0.0
    metabolic_profit_with_loss: float = 0.0
    irreversible_metrics: List[str] = field(default_factory=list)
    warnings: List[str] = field(default_factory=list)


def basin_trajectory_verdict(basins: Dict[str, BasinState]) -> str:
    """Aggregate direction across all basin trajectories."""
    deg = 0
    reg = 0
    total = 0
    for basin in basins.values():
        for _, t in basin.trajectory.items():
            total += 1
            if t < 0:
                deg += 1
            elif t > 0:
                reg += 1
    if total == 0:
        return "STABLE"
    if deg > reg:
        return "DEGRADING"
    if reg > deg:
        return "IMPROVING"
    return "STABLE"


def min_time_to_red(basins: Dict[str, BasinState]) -> Optional[float]:
    """Shortest time_to_cliff across all basin metrics, or None."""
    best: Optional[float] = None
    for basin in basins.values():
        for key in basin.state.keys():
            ttf = basin.time_to_cliff(key)
            if ttf is None:
                continue
            if best is None or ttf < best:
                best = ttf
    return best


def yield_signal(flow: MetabolicFlow, ttr: Optional[float]) -> str:
    """GREEN / AMBER / RED / BLACK.

    BLACK if any basin metric is irreversible.
    RED if metabolic profit < 0, or ttr <= 1, or debt > reported profit.
    AMBER if metabolic < half of reported, or ttr <= 5, or regen gap > 0.
    GREEN otherwise.
    """
    if flow.has_irreversibility():
        return "BLACK"

    mp = flow.metabolic_profit()
    rp = flow.reported_profit()
    gap = flow.regeneration_gap()

    if mp < 0:
        return "RED"
    if ttr is not None and ttr <= 1.0:
        return "RED"
    if flow.regeneration_debt > max(rp, 1.0):
        return "RED"

    if rp > 0 and not isinf(mp) and mp < 0.5 * rp:
        return "AMBER"
    if ttr is not None and ttr <= 5.0:
        return "AMBER"
    if gap > 0:
        return "AMBER"
    return "GREEN"


def assess(
    basins: Dict[str, BasinState],
    flow: MetabolicFlow,
    extraordinary_revenue_threshold: float = 0.05,
    extraordinary_min_absolute: float = 0.0,
) -> Verdict:
    """Produce a reproducible verdict from the current period's inputs."""
    traj = basin_trajectory_verdict(basins)
    ttr = min_time_to_red(basins)
    signal = yield_signal(flow, ttr)
    rp = flow.reported_profit()
    mp = flow.metabolic_profit()
    mp_full = flow.metabolic_profit_with_loss()
    profit_gap = inf if isinf(mp) else rp - mp
    extraordinary = flow.is_extraordinary_loss_material(
        revenue_threshold=extraordinary_revenue_threshold,
        min_absolute=extraordinary_min_absolute,
    )

    warnings: List[str] = []
    if flow.environment_loss > 0:
        base = (
            f"environment loss this period: {flow.environment_loss:.2f} {UNIT} "
            "(irreversible, nonrecurring)"
        )
        if extraordinary:
            pct = (
                f"{flow.environment_loss / flow.revenue * 100:.1f}% of revenue"
                if flow.revenue > 0
                else "n/a"
            )
            warnings.append(f"EXTRAORDINARY ITEM: {base}, {pct}")
        else:
            warnings.append(base)
    if flow.cumulative_environment_loss > 0:
        warnings.append(
            f"cumulative environment loss to date: "
            f"{flow.cumulative_environment_loss:.2f} {UNIT} (unrecoverable)"
        )
    if flow.irreversible_metrics:
        warnings.append("IRREVERSIBLE: " + ", ".join(flow.irreversible_metrics))
    if flow.regeneration_gap() > 0:
        g = flow.regeneration_gap()
        warnings.append(
            f"regeneration underpaid by {'infinite' if isinf(g) else f'{g:.2f}'}"
        )
    if traj == "DEGRADING":
        warnings.append("basin trajectory is degrading across majority of metrics")
    if ttr is not None and ttr <= 1.0:
        warnings.append(f"cliff crossing imminent: time_to_red = {ttr:.2f}")
    if rp > 0 and (isinf(mp) or mp < 0):
        warnings.append(
            "reported profit is positive but metabolic profit is non-positive -- "
            "firm is consuming its own basin"
        )

    forced = inf if isinf(flow.regeneration_required) else (
        flow.regeneration_required + flow.cascade_burn
    )

    return Verdict(
        sustainable_yield_signal=signal,
        basin_trajectory=traj,
        time_to_red=ttr,
        forced_drawdown=forced,
        regeneration_debt=flow.regeneration_debt,
        metabolic_profit=mp,
        reported_profit=rp,
        profit_gap=profit_gap,
        extraordinary_item_flagged=extraordinary,
        extraordinary_item_amount=flow.environment_loss,
        metabolic_profit_with_loss=mp_full,
        irreversible_metrics=list(flow.irreversible_metrics),
        warnings=warnings,
    )


# ---------------------------------------------------------------------------
# Bridge: translate a resilience_stack cascade score to a verdict tier
# ---------------------------------------------------------------------------


def classify_cascade_score(score: float) -> str:
    """Map a 0-10 cascade vulnerability score (from resilience_stack) to
    a GREEN/AMBER/RED/BLACK tier.

    The upstream verdict layer works on basin states and a MetabolicFlow;
    the Inversion corpus usually only has the scalar score from
    ResilienceStack. This bridge keeps the tier language consistent
    across the combined audit.
    """
    if score >= 9:
        return "BLACK"
    if score >= 6:
        return "RED"
    if score >= 3:
        return "AMBER"
    return "GREEN"


# ---------------------------------------------------------------------------
# Demo scenarios for Inversion's domain
# ---------------------------------------------------------------------------


def _demo_healthy() -> tuple[Dict[str, BasinState], MetabolicFlow]:
    basins = {
        "corpus": BasinState(
            name="ai_training_corpus",
            basin_type="information",
            state={"diversity": 0.85, "physics_alignment": 0.92},
            capacity={"diversity": 1.0, "physics_alignment": 1.0},
            trajectory={"diversity": 0.01, "physics_alignment": 0.005},
            cliff_thresholds={"diversity": 0.3, "physics_alignment": 0.4},
        ),
        "biology": BasinState(
            name="biological_integrity",
            basin_type="biology",
            state={"maternal_survival": 0.98, "genetic_variation": 0.90},
            capacity={"maternal_survival": 1.0, "genetic_variation": 1.0},
            trajectory={"maternal_survival": 0.0, "genetic_variation": 0.002},
            cliff_thresholds={"maternal_survival": 0.80, "genetic_variation": 0.40},
        ),
    }
    flow = MetabolicFlow(
        revenue=100.0,
        direct_operating_cost=40.0,
        regeneration_paid=20.0,
        regeneration_required=20.0,
        cascade_burn=0.0,
    )
    return basins, flow


def _demo_inverted() -> tuple[Dict[str, BasinState], MetabolicFlow]:
    basins = {
        "corpus": BasinState(
            name="ai_training_corpus",
            basin_type="information",
            state={"diversity": 0.35, "physics_alignment": 0.42},
            capacity={"diversity": 1.0, "physics_alignment": 1.0},
            trajectory={"diversity": -0.04, "physics_alignment": -0.03},
            cliff_thresholds={"diversity": 0.3, "physics_alignment": 0.4},
        ),
        "biology": BasinState(
            name="biological_integrity",
            basin_type="biology",
            state={"maternal_survival": 0.88, "genetic_variation": 0.55},
            capacity={"maternal_survival": 1.0, "genetic_variation": 1.0},
            trajectory={"maternal_survival": -0.02, "genetic_variation": -0.01},
            cliff_thresholds={"maternal_survival": 0.80, "genetic_variation": 0.40},
        ),
    }
    flow = MetabolicFlow(
        revenue=100.0,
        direct_operating_cost=40.0,
        regeneration_paid=10.0,
        regeneration_required=45.0,
        cascade_burn=15.0,
        regeneration_debt=120.0,
        environment_loss=6.5,
    )
    return basins, flow


def _demo_irreversible() -> tuple[Dict[str, BasinState], MetabolicFlow]:
    basins, _ = _demo_inverted()
    flow = MetabolicFlow(
        revenue=100.0,
        direct_operating_cost=40.0,
        regeneration_paid=10.0,
        regeneration_required=inf,
        cascade_burn=30.0,
        regeneration_debt=inf,
        environment_loss=25.0,
        cumulative_environment_loss=140.0,
        irreversible_metrics=["corpus.physics_alignment", "biology.genetic_variation"],
    )
    return basins, flow


DEMOS = {
    "healthy": _demo_healthy,
    "inverted": _demo_inverted,
    "irreversible": _demo_irreversible,
}


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------


def _print_verdict(name: str, basins: Dict[str, BasinState], flow: MetabolicFlow) -> None:
    verdict = assess(basins, flow)
    print(f"=== {name} ===")
    print(f"  signal:                {verdict.sustainable_yield_signal}")
    print(f"  basin_trajectory:      {verdict.basin_trajectory}")
    print(f"  time_to_red:           {verdict.time_to_red}")
    print(f"  reported_profit:       {verdict.reported_profit:.2f} {UNIT}")
    mp = verdict.metabolic_profit
    print(f"  metabolic_profit:      {'-inf' if isinf(mp) else f'{mp:.2f}'} {UNIT}")
    gap = verdict.profit_gap
    print(f"  profit_gap:            {'inf' if isinf(gap) else f'{gap:.2f}'} {UNIT}")
    print(f"  forced_drawdown:       "
          f"{'inf' if isinf(verdict.forced_drawdown) else f'{verdict.forced_drawdown:.2f}'} {UNIT}")
    if verdict.extraordinary_item_flagged:
        print(f"  extraordinary_item:    {verdict.extraordinary_item_amount:.2f} {UNIT}")
    if verdict.irreversible_metrics:
        print(f"  irreversible_metrics:  {verdict.irreversible_metrics}")
    if verdict.warnings:
        print("  warnings:")
        for w in verdict.warnings:
            print(f"    - {w}")
    print()


def _main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[1])
    parser.add_argument(
        "--demo",
        choices=sorted(DEMOS) + ["all"],
        default="all",
        help="run a built-in scenario (default: all three)",
    )
    parser.add_argument("--json", action="store_true", help="emit JSON")
    parser.add_argument(
        "--classify",
        type=float,
        metavar="SCORE",
        help="translate a cascade_vulnerability_score (0-10) to a verdict tier and exit",
    )
    args = parser.parse_args(argv)

    if args.classify is not None:
        tier = classify_cascade_score(args.classify)
        if args.json:
            print(json.dumps({"cascade_score": args.classify, "tier": tier}))
        else:
            print(f"cascade_score={args.classify:.2f} -> {tier}")
        return 0

    names = list(DEMOS) if args.demo == "all" else [args.demo]

    if args.json:
        out = {}
        for name in names:
            basins, flow = DEMOS[name]()
            verdict = assess(basins, flow)
            out[name] = asdict(verdict)
            # Replace inf with the string "inf" for JSON cleanliness
            for k, v in list(out[name].items()):
                if isinstance(v, float) and isinf(v):
                    out[name][k] = "inf" if v > 0 else "-inf"
        print(json.dumps(out, indent=2))
    else:
        for name in names:
            basins, flow = DEMOS[name]()
            _print_verdict(name, basins, flow)

    return 0


if __name__ == "__main__":
    sys.exit(_main())
