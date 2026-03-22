#!/usr/bin/env python3
"""
Systems Dynamics Simulation

Models feedback loops, homogeneity enforcement, and collapse trajectories
as described in the Institutional Inversion framework.

Three interconnected systems are simulated:
  1. Diversity Index    — measure of variation/adaptive capacity in a population
  2. Feedback Strength  — ability of the system to self-correct
  3. System Health      — overall viability (collapses when it hits zero)

Homogeneity enforcement acts as an external force that suppresses diversity
and weakens feedback loops, accelerating collapse.
"""

from __future__ import annotations

import argparse
import math
import sys
from dataclasses import dataclass, field


@dataclass
class SystemState:
    """Snapshot of the system at a given time step."""
    tick: int = 0
    diversity: float = 1.0        # 0.0 = total homogeneity, 1.0 = full diversity
    feedback: float = 1.0         # 0.0 = no self-correction, 1.0 = full feedback
    health: float = 1.0           # 0.0 = collapsed, 1.0 = thriving
    enforcement: float = 0.0      # external homogeneity pressure (0.0–1.0)
    collapsed: bool = False

    def summary(self) -> str:
        bar = lambda v: "#" * int(v * 20) + "." * (20 - int(v * 20))
        status = "COLLAPSED" if self.collapsed else "active"
        return (
            f"t={self.tick:>4}  "
            f"diversity [{bar(self.diversity)}] {self.diversity:.3f}  "
            f"feedback [{bar(self.feedback)}] {self.feedback:.3f}  "
            f"health [{bar(self.health)}] {self.health:.3f}  "
            f"enforcement={self.enforcement:.2f}  "
            f"[{status}]"
        )


@dataclass
class SimConfig:
    """Tunable parameters for the simulation."""
    ticks: int = 100

    # How quickly enforcement ramps up (logistic curve midpoint & steepness)
    enforcement_onset: int = 20       # tick at which enforcement reaches 50%
    enforcement_steepness: float = 0.15
    enforcement_max: float = 0.9      # ceiling for enforcement pressure

    # How strongly enforcement suppresses diversity per tick
    diversity_suppression_rate: float = 0.03

    # Feedback degrades when diversity drops below this threshold
    feedback_diversity_floor: float = 0.5

    # Health recovery/decay rates
    health_recovery_rate: float = 0.02   # natural healing when feedback exists
    health_decay_base: float = 0.01      # baseline decay
    health_collapse_threshold: float = 0.05

    # Natural diversity recovery (adaptation) — diminished by enforcement
    diversity_recovery_rate: float = 0.01


def enforcement_curve(tick: int, cfg: SimConfig) -> float:
    """Logistic ramp-up of homogeneity enforcement over time."""
    x = cfg.enforcement_steepness * (tick - cfg.enforcement_onset)
    return cfg.enforcement_max / (1.0 + math.exp(-x))


def step(state: SystemState, cfg: SimConfig) -> SystemState:
    """Advance the simulation by one tick."""
    if state.collapsed:
        return state

    t = state.tick + 1
    enf = enforcement_curve(t, cfg)

    # --- Diversity ---
    # Enforcement suppresses diversity; natural adaptation recovers it
    diversity_loss = cfg.diversity_suppression_rate * enf
    diversity_gain = cfg.diversity_recovery_rate * state.feedback * (1.0 - enf)
    diversity = max(0.0, min(1.0, state.diversity - diversity_loss + diversity_gain))

    # --- Feedback ---
    # Feedback degrades as diversity falls below the floor
    if diversity < cfg.feedback_diversity_floor:
        ratio = diversity / cfg.feedback_diversity_floor
        feedback = state.feedback * (0.98 + 0.02 * ratio)  # slow decay
    else:
        feedback = min(1.0, state.feedback + 0.005)  # slow recovery
    feedback = max(0.0, feedback)

    # --- Health ---
    # Recovery proportional to feedback * diversity; decay from enforcement + low diversity
    recovery = cfg.health_recovery_rate * feedback * diversity
    decay = cfg.health_decay_base + 0.05 * enf * (1.0 - diversity)
    health = max(0.0, min(1.0, state.health + recovery - decay))

    collapsed = health <= cfg.health_collapse_threshold

    return SystemState(
        tick=t,
        diversity=diversity,
        feedback=feedback,
        health=health,
        enforcement=enf,
        collapsed=collapsed,
    )


def run_simulation(cfg: SimConfig, quiet: bool = False) -> list[SystemState]:
    """Run the full simulation and return state history."""
    history: list[SystemState] = []
    state = SystemState()
    history.append(state)

    if not quiet:
        print("=" * 110)
        print("  SYSTEMS DYNAMICS SIMULATION — Homogeneity Enforcement & Collapse Trajectory")
        print("=" * 110)
        print(state.summary())

    for _ in range(cfg.ticks):
        state = step(state, cfg)
        history.append(state)
        if not quiet:
            print(state.summary())
        if state.collapsed:
            if not quiet:
                print(f"\n  *** SYSTEM COLLAPSED at t={state.tick} ***")
                print(f"  Diversity was {state.diversity:.3f}, feedback was {state.feedback:.3f}")
                print(f"  Enforcement pressure at collapse: {state.enforcement:.3f}")
            break

    if not quiet and not state.collapsed:
        print(f"\n  System survived {cfg.ticks} ticks.")
        print(f"  Final diversity={state.diversity:.3f}, feedback={state.feedback:.3f}, health={state.health:.3f}")

    return history


def run_comparison(cfg: SimConfig) -> None:
    """Run three scenarios side-by-side: no enforcement, moderate, and aggressive."""
    scenarios = [
        ("No enforcement", SimConfig(**{**cfg.__dict__, "enforcement_max": 0.0})),
        ("Moderate enforcement", SimConfig(**{**cfg.__dict__, "enforcement_max": 0.5})),
        ("Aggressive enforcement", SimConfig(**{**cfg.__dict__, "enforcement_max": 0.95})),
    ]

    print("=" * 80)
    print("  SCENARIO COMPARISON")
    print("=" * 80)

    for name, scfg in scenarios:
        history = run_simulation(scfg, quiet=True)
        final = history[-1]
        if final.collapsed:
            outcome = f"COLLAPSED at t={final.tick}"
        else:
            outcome = f"Survived (health={final.health:.3f})"
        print(f"\n  {name:30s} => {outcome}")
        print(f"    Final diversity={final.diversity:.3f}  feedback={final.feedback:.3f}  enforcement={final.enforcement:.3f}")

    print()


def main() -> None:
    parser = argparse.ArgumentParser(description="Systems dynamics collapse simulation")
    parser.add_argument("--ticks", type=int, default=100, help="Number of time steps (default: 100)")
    parser.add_argument("--enforcement-max", type=float, default=0.9, help="Max enforcement pressure 0.0-1.0 (default: 0.9)")
    parser.add_argument("--enforcement-onset", type=int, default=20, help="Tick at which enforcement reaches 50%% (default: 20)")
    parser.add_argument("--compare", action="store_true", help="Run three scenarios side-by-side")
    parser.add_argument("--quiet", action="store_true", help="Only print final state")
    args = parser.parse_args()

    cfg = SimConfig(
        ticks=args.ticks,
        enforcement_max=args.enforcement_max,
        enforcement_onset=args.enforcement_onset,
    )

    if args.compare:
        run_comparison(cfg)
    else:
        run_simulation(cfg, quiet=args.quiet)


if __name__ == "__main__":
    main()
