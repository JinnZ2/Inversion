#!/usr/bin/env python3
"""
resource_flow_dynamics.py — Coupled resource flow dynamics simulation.

Models accumulation vs. circulation vs. coupling in single-pool and
multi-agent networked systems.  Tracks circulating resource (C),
hoarded/stored resource (H), and responsiveness (R, a coupling
efficiency between 0 and 1).

Single-pool model
    Minimal three-variable ODE: extraction drains C into H, release
    returns H to C, productivity amplifies C proportional to R, and
    dissipation removes C.  Responsiveness degrades under load and
    recovers toward 1.

Multi-agent networked model
    N agents each carry their own (C, H, R) and are linked by a
    row-stochastic adjacency matrix.  Diffusive flow moves C from
    high- to low-concentration agents.  Designated "hoarder" agents
    can have elevated extraction and suppressed release.

Analysis utilities compute peak throughput, collapse detection
(throughput < 20 % of peak), and Gini coefficients for terminal
distributions.

References
----------
* Lotka–Volterra resource competition — Volterra (1926), Gause (1934).
* Gini coefficient — Gini, C. (1912).  "Variabilità e mutabilità."
* Diffusion on networks — Masuda, Porter & Lambiotte (2017), "Random
  walks and diffusion on networks", Physics Reports 716–717.

Usage
-----
    python3 scripts/resource_flow_dynamics.py --mode single --steps 2000
    python3 scripts/resource_flow_dynamics.py --mode network --steps 800 --agents 30
    python3 scripts/resource_flow_dynamics.py --mode network --json
    python3 scripts/resource_flow_dynamics.py --help
"""

import argparse
import json
import math
import random
import sys
from dataclasses import dataclass, field
from typing import Dict, List, Any, Optional, Tuple


# -----------------------------------------------------------------------
#  Numeric helpers (stdlib replacements for numpy operations)
# -----------------------------------------------------------------------

def _clip(value, lo, hi):
    """Clamp a scalar to [lo, hi]."""
    if lo is not None and value < lo:
        return lo
    if hi is not None and value > hi:
        return hi
    return value


def _vec_clip(vec, lo, hi):
    """Element-wise clamp a list of floats."""
    return [_clip(v, lo, hi) for v in vec]


def _vec_add(a, b):
    return [x + y for x, y in zip(a, b)]


def _vec_sub(a, b):
    return [x - y for x, y in zip(a, b)]


def _vec_mul(a, b):
    """Element-wise multiplication of two lists."""
    return [x * y for x, y in zip(a, b)]


def _vec_scale(a, s):
    return [x * s for x in a]


def _vec_div_scalar(a, s):
    return [x / s for x in a]


def _vec_full(n, val):
    return [val] * n


def _vec_sum(a):
    return sum(a)


def _vec_mean(a):
    return sum(a) / len(a) if a else 0.0


def _vec_min(a):
    return min(a)


def _vec_max(a):
    return max(a)


def _vec_argmax(a):
    return max(range(len(a)), key=lambda i: a[i])


def _vec_copy(a):
    return list(a)


def _vec_abs(a):
    return [abs(x) for x in a]


def _vec_sorted(a):
    return sorted(a)


def _make_row_stochastic(matrix, n):
    """Normalise each row to sum to 1 and zero the diagonal."""
    for i in range(n):
        s = sum(matrix[i])
        if s > 0:
            matrix[i] = [v / s for v in matrix[i]]
        matrix[i][i] = 0.0
    return matrix


def _random_adjacency(n, rng):
    """Create a random row-stochastic adjacency matrix (list of lists)."""
    mat = [[rng.random() for _ in range(n)] for _ in range(n)]
    return _make_row_stochastic(mat, n)


# -----------------------------------------------------------------------
#  Single-Pool Model
# -----------------------------------------------------------------------

@dataclass
class FlowParams:
    """Parameters for single-pool H/C/R dynamics."""
    alpha: float = 0.08    # extraction rate (C -> H)
    beta: float = 0.02     # release rate (H -> C)
    delta: float = 0.04    # productivity (C generates more C)
    gamma: float = 0.02    # dissipation (entropy loss from C)
    k1: float = 0.005      # responsiveness degradation rate
    k2: float = 0.010      # responsiveness recovery rate
    C_ref: float = 100.0   # reference C level for signal normalization
    dt: float = 0.1        # time step


@dataclass
class FlowState:
    """State of a single-pool system."""
    C: float = 100.0       # circulating resource
    H: float = 10.0        # hoarded/stored resource
    R: float = 1.0         # responsiveness (coupling efficiency, 0-1)


def step_single(state: FlowState, params: FlowParams) -> FlowState:
    """Advance single-pool system by one time step."""
    C, H, R = state.C, state.H, state.R
    dt = params.dt

    extraction = params.alpha * C
    release = params.beta * H
    productivity = params.delta * C * R
    dissipation = params.gamma * C
    signal = C / params.C_ref  # normalized coupling load (0-1 scale)

    dC = -extraction + release + productivity - dissipation
    dH = extraction - release
    dR = -params.k1 * signal + params.k2 * (1.0 - R)

    return FlowState(
        C=max(0, C + dC * dt),
        H=max(0, H + dH * dt),
        R=_clip(R + dR * dt, 0, 1),
    )


def run_single(
    params: FlowParams,
    initial: Optional[FlowState] = None,
    steps: int = 2000,
) -> Dict[str, Any]:
    """
    Run single-pool simulation.

    Returns
    -------
    dict with time series for C, H, R, throughput, and total resource.
    """
    state = initial or FlowState()
    history: Dict[str, list] = {
        "C": [], "H": [], "R": [], "throughput": [], "total": [],
    }

    for _ in range(steps):
        throughput = params.delta * state.C * state.R
        history["C"].append(state.C)
        history["H"].append(state.H)
        history["R"].append(state.R)
        history["throughput"].append(throughput)
        history["total"].append(state.C + state.H)
        state = step_single(state, params)

    return history


# -----------------------------------------------------------------------
#  Multi-Agent Networked Model
# -----------------------------------------------------------------------

@dataclass
class NetworkParams:
    """Parameters for multi-agent networked dynamics."""
    n_agents: int = 30
    kappa: float = 0.15          # network flow strength
    alpha: Optional[list] = None       # per-agent extraction rates
    beta: Optional[list] = None        # per-agent release rates
    delta: Optional[list] = None       # per-agent productivity
    gamma: Optional[list] = None       # per-agent dissipation
    k1: float = 0.004            # responsiveness degradation
    k2: float = 0.008            # responsiveness recovery
    C_ref: float = 50.0          # reference C level for signal normalization
    dt: float = 0.05
    adjacency: Optional[list] = None   # row-stochastic adjacency matrix

    def __post_init__(self):
        n = self.n_agents
        if self.alpha is None:
            self.alpha = _vec_full(n, 0.06)
        if self.beta is None:
            self.beta = _vec_full(n, 0.02)
        if self.delta is None:
            self.delta = _vec_full(n, 0.04)
        if self.gamma is None:
            self.gamma = _vec_full(n, 0.02)
        if self.adjacency is None:
            rng = random.Random(42)
            self.adjacency = _random_adjacency(n, rng)


@dataclass
class NetworkState:
    """State of a multi-agent network."""
    C: list   # circulating per agent
    H: list   # stored per agent
    R: list   # responsiveness per agent

    @classmethod
    def default(cls, n: int, seed: int = 42) -> "NetworkState":
        rng = random.Random(seed)
        C = [_clip(50 + 10 * rng.gauss(0, 1), 10, None) for _ in range(n)]
        H = _vec_full(n, 10.0)
        R = _vec_full(n, 1.0)
        return cls(C=C, H=H, R=R)


def network_flow(C: list, A: list, kappa: float) -> list:
    """Compute net flow for each agent from diffusion on adjacency."""
    n = len(C)
    result = [0.0] * n
    for i in range(n):
        for j in range(n):
            # F_ij = kappa * A_ij * (C_i - C_j)
            f = kappa * A[i][j] * (C[i] - C[j])
            # inflow from j's perspective, outflow from i's perspective
            result[j] += f
            result[i] -= f
    return result


def step_network(state: NetworkState, params: NetworkParams) -> NetworkState:
    """Advance network by one time step."""
    C, H, R = state.C, state.H, state.R
    dt = params.dt

    extraction = _vec_mul(params.alpha, C)
    release = _vec_mul(params.beta, H)
    productivity = _vec_mul(_vec_mul(params.delta, C), R)
    dissipation = _vec_mul(params.gamma, C)
    net_flow = network_flow(C, params.adjacency, params.kappa)
    signal = _vec_div_scalar(C, params.C_ref)

    # dC = -extraction + release + productivity - dissipation + net_flow
    dC = _vec_add(
        _vec_add(_vec_sub(_vec_sub([0.0] * len(C), extraction), dissipation),
                 release),
        _vec_add(productivity, net_flow),
    )
    dH = _vec_sub(extraction, release)
    # dR = -k1 * signal + k2 * (1 - R)
    dR = _vec_add(
        _vec_scale(signal, -params.k1),
        _vec_scale(_vec_sub(_vec_full(len(R), 1.0), R), params.k2),
    )

    return NetworkState(
        C=_vec_clip(_vec_add(C, _vec_scale(dC, dt)), 0, None),
        H=_vec_clip(_vec_add(H, _vec_scale(dH, dt)), 0, None),
        R=_vec_clip(_vec_add(R, _vec_scale(dR, dt)), 0, 1),
    )


def run_network(
    params: NetworkParams,
    initial: Optional[NetworkState] = None,
    steps: int = 800,
    hoarder_indices: Optional[List[int]] = None,
    hoarder_alpha: float = 0.10,
    hoarder_beta: float = 0.005,
    perturbation_step: Optional[int] = None,
    perturbation_fraction: float = 0.3,
    perturbation_sigma: float = 2.0,
    seed: int = 42,
) -> Dict[str, Any]:
    """
    Run multi-agent network simulation.

    Parameters
    ----------
    hoarder_indices : list[int], optional
        Agents with elevated extraction and reduced release.
    perturbation_step : int, optional
        Step at which to inject random perturbation.

    Returns
    -------
    dict with aggregate time series and per-agent final state.
    """
    rng = random.Random(seed)

    # Apply hoarder parameters
    if hoarder_indices:
        for i in hoarder_indices:
            params.alpha[i] = hoarder_alpha
            params.beta[i] = hoarder_beta

    state = initial or NetworkState.default(params.n_agents, seed)

    agg: Dict[str, list] = {
        "total_C": [], "total_H": [], "total_throughput": [],
        "mean_R": [], "min_R": [],
    }

    for t in range(steps):
        # Perturbation
        if perturbation_step is not None and t == perturbation_step:
            count = max(1, int(params.n_agents * perturbation_fraction))
            indices = rng.sample(range(params.n_agents), count)
            for idx in indices:
                state.C[idx] += rng.gauss(0, perturbation_sigma)
            state.C = _vec_clip(state.C, 0, None)

        throughput = _vec_mul(_vec_mul(params.delta, state.C), state.R)

        agg["total_C"].append(_vec_sum(state.C))
        agg["total_H"].append(_vec_sum(state.H))
        agg["total_throughput"].append(_vec_sum(throughput))
        agg["mean_R"].append(_vec_mean(state.R))
        agg["min_R"].append(_vec_min(state.R))

        state = step_network(state, params)

    return {
        "aggregates": agg,
        "final_state": {
            "C": _vec_copy(state.C),
            "H": _vec_copy(state.H),
            "R": _vec_copy(state.R),
        },
        "params": {
            "n_agents": params.n_agents,
            "kappa": params.kappa,
            "k1": params.k1,
            "k2": params.k2,
            "hoarder_indices": hoarder_indices or [],
        },
    }


# -----------------------------------------------------------------------
#  Analysis Utilities
# -----------------------------------------------------------------------

def diagnose_single(history: Dict[str, list]) -> Dict[str, Any]:
    """Diagnose single-pool run."""
    C, H, R = history["C"], history["H"], history["R"]
    tp = history["throughput"]

    peak_throughput_t = _vec_argmax(tp)
    final_R = float(R[-1])
    total_accumulated = float(H[-1])
    total_circulating = float(C[-1])

    # Detect collapse: throughput drops below 20% of peak
    peak_tp = _vec_max(tp)
    collapse_t = None
    for t in range(peak_throughput_t, len(tp)):
        if tp[t] < 0.2 * peak_tp:
            collapse_t = t
            break

    return {
        "peak_throughput": float(peak_tp),
        "peak_throughput_time": peak_throughput_t,
        "final_responsiveness": final_R,
        "final_stored": total_accumulated,
        "final_circulating": total_circulating,
        "collapse_time": collapse_t,
        "regime": (
            "collapsed" if collapse_t is not None
            else "degraded" if final_R < 0.3
            else "stable"
        ),
    }


def diagnose_network(result: Dict[str, Any]) -> Dict[str, Any]:
    """Diagnose network run."""
    agg = result["aggregates"]
    tp = agg["total_throughput"]
    mean_R = agg["mean_R"]

    peak_tp = float(_vec_max(tp))
    peak_t = _vec_argmax(tp)
    final_tp = float(tp[-1])

    collapse_t = None
    for t in range(peak_t, len(tp)):
        if tp[t] < 0.2 * peak_tp:
            collapse_t = t
            break

    final = result["final_state"]
    gini_C = _gini(final["C"])
    gini_H = _gini(final["H"])

    return {
        "peak_throughput": peak_tp,
        "final_throughput": final_tp,
        "throughput_retention": final_tp / peak_tp if peak_tp > 0 else 0,
        "final_mean_R": float(mean_R[-1]),
        "collapse_time": collapse_t,
        "gini_C": gini_C,
        "gini_H": gini_H,
        "regime": (
            "collapsed" if collapse_t is not None
            else "degraded" if mean_R[-1] < 0.3
            else "stable"
        ),
    }


def _gini(arr: list) -> float:
    """Gini coefficient (0 = equal, 1 = one agent has everything)."""
    arr = [abs(x) for x in arr]
    total = sum(arr)
    if total == 0:
        return 0.0
    sorted_arr = sorted(arr)
    n = len(sorted_arr)
    weighted_sum = sum((i + 1) * v for i, v in enumerate(sorted_arr))
    return float((2 * weighted_sum / (n * total)) - (n + 1) / n)


# -----------------------------------------------------------------------
#  CLI
# -----------------------------------------------------------------------

def _format_diagnosis(diag: Dict[str, Any], label: str) -> str:
    """Format a diagnosis dict as human-readable text."""
    lines = [f"--- {label} ---"]
    for k, v in diag.items():
        if isinstance(v, float):
            lines.append(f"  {k}: {v:.6f}")
        else:
            lines.append(f"  {k}: {v}")
    return "\n".join(lines)


def main():
    parser = argparse.ArgumentParser(
        description="Coupled resource flow dynamics: accumulation vs "
                    "circulation vs coupling.  Single-pool and multi-agent "
                    "networked models with diagnosis utilities.",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=(
            "examples:\n"
            "  %(prog)s --mode single --steps 2000\n"
            "  %(prog)s --mode network --agents 30 --steps 800\n"
            "  %(prog)s --mode network --hoarders 0,1,2 --json\n"
        ),
    )
    parser.add_argument(
        "--mode", choices=["single", "network"], default="single",
        help="simulation mode (default: single)",
    )
    parser.add_argument(
        "--steps", type=int, default=None,
        help="number of time steps (default: 2000 single, 800 network)",
    )
    parser.add_argument(
        "--agents", type=int, default=30,
        help="number of agents for network mode (default: 30)",
    )
    parser.add_argument(
        "--hoarders", type=str, default=None,
        help="comma-separated agent indices to designate as hoarders",
    )
    parser.add_argument(
        "--hoarder-alpha", type=float, default=0.10,
        help="extraction rate for hoarder agents (default: 0.10)",
    )
    parser.add_argument(
        "--hoarder-beta", type=float, default=0.005,
        help="release rate for hoarder agents (default: 0.005)",
    )
    parser.add_argument(
        "--perturbation-step", type=int, default=None,
        help="step at which to inject random perturbation (network mode)",
    )
    parser.add_argument(
        "--seed", type=int, default=42,
        help="random seed (default: 42)",
    )
    parser.add_argument(
        "--json", action="store_true",
        help="output full results as JSON",
    )

    args = parser.parse_args()

    if args.mode == "single":
        steps = args.steps or 2000
        params = FlowParams()
        history = run_single(params, steps=steps)
        diag = diagnose_single(history)

        if args.json:
            json.dump({
                "mode": "single",
                "steps": steps,
                "diagnosis": diag,
                "history": {k: [round(x, 8) for x in v] for k, v in history.items()},
            }, sys.stdout, indent=2)
            print()
        else:
            print(_format_diagnosis(diag, "Single-Pool Diagnosis"))

    elif args.mode == "network":
        steps = args.steps or 800
        hoarder_indices = None
        if args.hoarders:
            hoarder_indices = [int(x.strip()) for x in args.hoarders.split(",")]

        params = NetworkParams(n_agents=args.agents)
        result = run_network(
            params,
            steps=steps,
            hoarder_indices=hoarder_indices,
            hoarder_alpha=args.hoarder_alpha,
            hoarder_beta=args.hoarder_beta,
            perturbation_step=args.perturbation_step,
            seed=args.seed,
        )
        diag = diagnose_network(result)

        if args.json:
            output = {
                "mode": "network",
                "steps": steps,
                "diagnosis": diag,
                "aggregates": {
                    k: [round(x, 8) for x in v]
                    for k, v in result["aggregates"].items()
                },
                "final_state": {
                    k: [round(x, 8) for x in v]
                    for k, v in result["final_state"].items()
                },
                "params": result["params"],
            }
            json.dump(output, sys.stdout, indent=2)
            print()
        else:
            print(_format_diagnosis(diag, "Network Diagnosis"))
            print(f"\n  agents: {args.agents}")
            if hoarder_indices:
                print(f"  hoarders: {hoarder_indices}")


if __name__ == "__main__":
    main()
