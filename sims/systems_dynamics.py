#!/usr/bin/env python3
"""
Systems Dynamics Simulation — Ecosystem Collapse Under Homogeneity Enforcement

Models a population of N competing species using discretized Lotka-Volterra
competition dynamics. Measures system state with established metrics:

  - Shannon Diversity Index:  H = -Σ pᵢ ln(pᵢ)
  - Pielou's Evenness:        E = H / ln(N)
  - Entropy Production Rate:  dH/dt = ΔH / Δt (diversity change velocity)
  - Algebraic Connectivity:   λ₂ of the graph Laplacian (Fiedler value)
  - Living Species Count:     species with abundance above extinction threshold

Homogeneity enforcement is modeled as increasing niche overlap in the
competition matrix α, driving competitive exclusion (Gause's principle).

References:
  - Lotka (1925), Volterra (1926): competition equations
  - Shannon (1948): information entropy
  - Pielou (1966): evenness index
  - Fiedler (1973): algebraic connectivity of graphs
  - May (1973): stability and complexity in model ecosystems
  - Kondepudi & Prigogine (1998): entropy production in non-equilibrium systems
"""

from __future__ import annotations

import argparse
import math
import random
import sys
from dataclasses import dataclass, field


# ---------------------------------------------------------------------------
# Linear algebra helpers (stdlib-only)
# ---------------------------------------------------------------------------

def mat_vec_mul(mat: list[list[float]], vec: list[float]) -> list[float]:
    """Multiply matrix by vector."""
    return [sum(row[j] * vec[j] for j in range(len(vec))) for row in mat]


def vec_dot(a: list[float], b: list[float]) -> float:
    return sum(ai * bi for ai, bi in zip(a, b))


def vec_norm(v: list[float]) -> float:
    return math.sqrt(vec_dot(v, v))


def vec_scale(v: list[float], s: float) -> list[float]:
    return [vi * s for vi in v]


def vec_sub(a: list[float], b: list[float]) -> list[float]:
    return [ai - bi for ai, bi in zip(a, b)]


def algebraic_connectivity(adj: list[list[float]], n: int, iters: int = 60) -> float:
    """
    Estimate λ₂ (Fiedler value) of the graph Laplacian via inverse iteration.

    The Laplacian L = D - A where D is the degree matrix. λ₁ = 0 with
    eigenvector proportional to 1⃗. We deflect against the zero-eigenspace
    and use power iteration on (μI - L) to find the largest eigenvalue of
    that shifted matrix, then λ₂ = μ - result.

    For small N (≤50) this converges well within 60 iterations.
    """
    if n <= 1:
        return 0.0

    # Build Laplacian
    L: list[list[float]] = [[0.0] * n for _ in range(n)]
    for i in range(n):
        deg = sum(adj[i])
        L[i][i] = deg
        for j in range(n):
            L[i][j] -= adj[i][j]

    # Shift: μ = 2 * max_degree (upper bound on spectrum)
    max_deg = max(L[i][i] for i in range(n))
    if max_deg == 0:
        return 0.0
    mu = 2.0 * max_deg

    # Shifted matrix M = μI - L
    M: list[list[float]] = [[0.0] * n for _ in range(n)]
    for i in range(n):
        for j in range(n):
            M[i][j] = -L[i][j]
        M[i][i] += mu

    # Power iteration with deflation against the constant eigenvector
    ones = [1.0 / math.sqrt(n)] * n  # normalized 1⃗
    # Start with a random vector orthogonal to ones
    rng = random.Random(42)
    v = [rng.gauss(0, 1) for _ in range(n)]
    # Orthogonalize against ones
    proj = vec_dot(v, ones)
    v = vec_sub(v, vec_scale(ones, proj))
    nrm = vec_norm(v)
    if nrm < 1e-12:
        return 0.0
    v = vec_scale(v, 1.0 / nrm)

    eigenvalue = 0.0
    for _ in range(iters):
        w = mat_vec_mul(M, v)
        # Deflect against ones
        proj = vec_dot(w, ones)
        w = vec_sub(w, vec_scale(ones, proj))
        nrm = vec_norm(w)
        if nrm < 1e-14:
            break
        eigenvalue = nrm
        v = vec_scale(w, 1.0 / nrm)

    lambda_2 = mu - eigenvalue
    return max(0.0, lambda_2)


# ---------------------------------------------------------------------------
# Ecosystem model
# ---------------------------------------------------------------------------

@dataclass
class EcosystemConfig:
    """Parameters for the ecosystem simulation."""
    n_species: int = 10
    ticks: int = 200
    dt: float = 0.1                   # Euler step size

    # Lotka-Volterra parameters
    r_min: float = 0.08               # min intrinsic growth rate
    r_max: float = 0.25               # max intrinsic growth rate
    k_min: float = 40.0               # min carrying capacity
    k_max: float = 150.0              # max carrying capacity (wide spread = niche differentiation)
    alpha_self: float = 1.0           # intraspecific competition (always 1)
    alpha_min: float = 0.15           # min interspecific competition (baseline niche overlap)
    alpha_max: float = 0.45           # max interspecific competition (baseline)

    # Enforcement parameters (logistic ramp)
    enforcement_onset: int = 40       # tick where enforcement reaches 50%
    enforcement_steepness: float = 0.08
    enforcement_max: float = 0.95     # drives α_ij toward 1.0

    # Thresholds
    extinction_threshold: float = 1.0
    collapse_species_min: int = 2     # collapse if fewer than this many survive
    collapse_evenness: float = 0.1    # collapse if evenness drops below this

    seed: int = 42


@dataclass
class EcosystemState:
    """Measurable state of the ecosystem at one time step."""
    tick: int
    populations: list[float]
    shannon_diversity: float          # H = -Σ pᵢ ln(pᵢ)
    evenness: float                   # E = H / ln(N)
    entropy_rate: float               # dH/dt = ΔH / Δt (nats per tick)
    algebraic_connectivity: float     # λ₂ (Fiedler value)
    living_species: int
    enforcement_level: float
    collapsed: bool

    def summary(self, compact: bool = False) -> str:
        dh_sign = "+" if self.entropy_rate >= 0 else ""
        if compact:
            return (
                f"t={self.tick:>4}  "
                f"species={self.living_species:>2}  "
                f"H={self.shannon_diversity:>5.3f}  "
                f"E={self.evenness:>5.3f}  "
                f"dH/dt={dh_sign}{self.entropy_rate:>7.4f}  "
                f"λ₂={self.algebraic_connectivity:>6.4f}  "
                f"enf={self.enforcement_level:.3f}"
                f"{'  COLLAPSED' if self.collapsed else ''}"
            )
        pop_str = " ".join(f"{x:6.1f}" for x in self.populations)
        return (
            f"t={self.tick:>4}  "
            f"pop=[{pop_str}]  "
            f"H={self.shannon_diversity:.3f}  "
            f"E={self.evenness:.3f}  "
            f"dH/dt={dh_sign}{self.entropy_rate:.4f}  "
            f"λ₂={self.algebraic_connectivity:.4f}  "
            f"alive={self.living_species}  "
            f"enf={self.enforcement_level:.3f}"
            f"{'  COLLAPSED' if self.collapsed else ''}"
        )


def shannon_diversity(populations: list[float]) -> tuple[float, float]:
    """
    Compute Shannon diversity H and evenness E.

    Evenness is normalized against ln(N_total), not ln(N_alive),
    so that species loss is reflected in the evenness measure.
    """
    total = sum(populations)
    n_total = len(populations)
    if total <= 0 or n_total <= 1:
        return 0.0, 0.0
    h = 0.0
    for x in populations:
        if x > 0:
            p = x / total
            h -= p * math.log(p)
    h_max = math.log(n_total)  # max possible diversity across ALL species
    e = h / h_max if h_max > 0 else 0.0
    return h, e


def build_alive_adjacency(populations: list[float], threshold: float) -> tuple[list[list[float]], int]:
    """
    Build adjacency matrix over the subgraph of living species only.
    Returns (adjacency_matrix, n_alive). All living species are
    pairwise connected (complete subgraph), representing the active
    interaction network.
    """
    alive_indices = [i for i, x in enumerate(populations) if x > threshold]
    n_alive = len(alive_indices)
    if n_alive <= 1:
        return [[0.0]], n_alive
    # Complete graph among living species
    adj: list[list[float]] = [[0.0] * n_alive for _ in range(n_alive)]
    for i in range(n_alive):
        for j in range(i + 1, n_alive):
            adj[i][j] = 1.0
            adj[j][i] = 1.0
    return adj, n_alive


def enforcement_level(tick: int, cfg: EcosystemConfig) -> float:
    """Logistic ramp of homogeneity enforcement."""
    x = cfg.enforcement_steepness * (tick - cfg.enforcement_onset)
    return cfg.enforcement_max / (1.0 + math.exp(-x))


def measure_state(
    tick: int, populations: list[float], enf: float, cfg: EcosystemConfig,
    prev_h: float = 0.0, dt: float = 1.0,
) -> EcosystemState:
    """Compute all metrics for the current population state.

    Entropy production rate dH/dt is the discrete derivative of Shannon
    diversity with respect to simulation time. Sustained negative dH/dt
    indicates irreversible diversity loss — the thermodynamic arrow
    pointing toward system collapse (Kondepudi & Prigogine, 1998).
    """
    h, e = shannon_diversity(populations)
    entropy_rate = (h - prev_h) / dt if dt > 0 else 0.0
    living = sum(1 for x in populations if x > cfg.extinction_threshold)
    adj, n_alive = build_alive_adjacency(populations, cfg.extinction_threshold)
    lam2 = algebraic_connectivity(adj, n_alive)
    collapsed = living < cfg.collapse_species_min or e < cfg.collapse_evenness
    return EcosystemState(
        tick=tick,
        populations=list(populations),
        shannon_diversity=h,
        evenness=e,
        entropy_rate=entropy_rate,
        algebraic_connectivity=lam2,
        living_species=living,
        enforcement_level=enf,
        collapsed=collapsed,
    )


def run_simulation(cfg: EcosystemConfig, quiet: bool = False) -> list[EcosystemState]:
    """
    Run the Lotka-Volterra competition simulation.

    Each tick:
      1. Compute enforcement level (logistic curve).
      2. Adjust competition matrix: α_ij(t) = α_ij(0)·(1-enf) + 1.0·enf
         (enforcement drives niche overlap toward 1.0, triggering Gause exclusion).
      3. Euler-step the LV equations: dx_i/dt = r_i·x_i·(1 - Σ_j α_ij·x_j / K_i)
      4. Apply extinction threshold.
      5. Measure Shannon diversity, evenness, algebraic connectivity.
    """
    rng = random.Random(cfg.seed)
    n = cfg.n_species

    # Initialize species parameters
    r = [rng.uniform(cfg.r_min, cfg.r_max) for _ in range(n)]
    k = [rng.uniform(cfg.k_min, cfg.k_max) for _ in range(n)]

    # Baseline competition matrix (before enforcement)
    alpha_base: list[list[float]] = [[0.0] * n for _ in range(n)]
    for i in range(n):
        for j in range(n):
            if i == j:
                alpha_base[i][j] = cfg.alpha_self
            else:
                alpha_base[i][j] = rng.uniform(cfg.alpha_min, cfg.alpha_max)

    # Initial populations: near carrying capacity with some noise
    x = [ki * rng.uniform(0.7, 1.0) for ki in k]

    history: list[EcosystemState] = []
    state = measure_state(0, x, 0.0, cfg, prev_h=0.0, dt=cfg.dt)
    history.append(state)

    if not quiet:
        print("=" * 95)
        print("  LOTKA-VOLTERRA ECOSYSTEM SIMULATION")
        print(f"  {n} species, {cfg.ticks} ticks, dt={cfg.dt}")
        print(f"  Enforcement: max={cfg.enforcement_max}, onset=t{cfg.enforcement_onset}")
        print("=" * 95)
        print(state.summary(compact=True))

    for tick in range(1, cfg.ticks + 1):
        enf = enforcement_level(tick, cfg)

        # Current competition matrix under enforcement
        alpha: list[list[float]] = [[0.0] * n for _ in range(n)]
        for i in range(n):
            for j in range(n):
                if i == j:
                    alpha[i][j] = cfg.alpha_self
                else:
                    # Enforcement drives off-diagonal α toward 1.0 (perfect niche overlap)
                    alpha[i][j] = alpha_base[i][j] * (1.0 - enf) + 1.0 * enf

        # Euler step: dx_i/dt = r_i * x_i * (1 - sum_j(alpha_ij * x_j) / K_i)
        dx = [0.0] * n
        for i in range(n):
            if x[i] <= 0:
                continue
            competition_sum = sum(alpha[i][j] * x[j] for j in range(n))
            dx[i] = r[i] * x[i] * (1.0 - competition_sum / k[i])

        # Update populations
        for i in range(n):
            x[i] = max(0.0, x[i] + cfg.dt * dx[i])
            if x[i] < cfg.extinction_threshold:
                x[i] = 0.0  # extinct

        prev_h = history[-1].shannon_diversity
        state = measure_state(tick, x, enf, cfg, prev_h=prev_h, dt=cfg.dt)
        history.append(state)

        if not quiet and (tick % 10 == 0 or state.collapsed):
            print(state.summary(compact=True))

        if state.collapsed:
            if not quiet:
                print(f"\n  *** ECOSYSTEM COLLAPSED at t={tick} ***")
                print(f"  Living species: {state.living_species}/{n}")
                print(f"  Shannon diversity: {state.shannon_diversity:.4f}")
                print(f"  Evenness: {state.evenness:.4f}")
                print(f"  Algebraic connectivity: {state.algebraic_connectivity:.4f}")
                survivors = [(i, x[i]) for i in range(n) if x[i] > 0]
                if survivors:
                    print(f"  Survivors: {', '.join(f'sp{i}({pop:.1f})' for i, pop in survivors)}")
            break

    if not quiet and not state.collapsed:
        print(f"\n  Ecosystem survived {cfg.ticks} ticks.")
        final = history[-1]
        min_dh = min(s.entropy_rate for s in history)
        min_dh_tick = next(s.tick for s in history if s.entropy_rate == min_dh)
        print(f"  Shannon H={final.shannon_diversity:.4f}, Evenness={final.evenness:.4f}")
        print(f"  dH/dt={final.entropy_rate:+.4f} (peak loss: {min_dh:.4f} at t={min_dh_tick})")
        print(f"  λ₂={final.algebraic_connectivity:.4f}, Living species={final.living_species}/{n}")

    return history


def run_comparison(cfg: EcosystemConfig) -> None:
    """Compare three enforcement scenarios."""
    scenarios = [
        ("No enforcement (control)", 0.0),
        ("Moderate enforcement", 0.5),
        ("Aggressive enforcement", 0.95),
    ]

    print("=" * 80)
    print("  SCENARIO COMPARISON — Lotka-Volterra Ecosystem")
    print("=" * 80)

    for name, enf_max in scenarios:
        scfg = EcosystemConfig(
            **{**cfg.__dict__, "enforcement_max": enf_max}
        )
        history = run_simulation(scfg, quiet=True)
        final = history[-1]

        if final.collapsed:
            outcome = f"COLLAPSED at t={final.tick}"
        else:
            outcome = f"Survived {cfg.ticks} ticks"

        # Compute peak entropy loss rate across the run
        min_dh = min(s.entropy_rate for s in history)
        min_dh_tick = next(s.tick for s in history if s.entropy_rate == min_dh)

        dh_sign = "+" if final.entropy_rate >= 0 else ""
        print(f"\n  {name}")
        print(f"    Outcome: {outcome}")
        print(f"    Species alive: {final.living_species}/{cfg.n_species}")
        print(f"    Shannon H = {final.shannon_diversity:.4f}")
        print(f"    Evenness  = {final.evenness:.4f}")
        print(f"    dH/dt     = {dh_sign}{final.entropy_rate:.4f}  (peak loss: {min_dh:.4f} at t={min_dh_tick})")
        print(f"    λ₂        = {final.algebraic_connectivity:.4f}")

    print()


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Lotka-Volterra ecosystem collapse simulation"
    )
    parser.add_argument("--species", type=int, default=10, help="Number of species (default: 10)")
    parser.add_argument("--ticks", type=int, default=200, help="Time steps (default: 200)")
    parser.add_argument("--dt", type=float, default=0.1, help="Euler step size (default: 0.1)")
    parser.add_argument("--enforcement-max", type=float, default=0.95, help="Max enforcement 0-1 (default: 0.95)")
    parser.add_argument("--enforcement-onset", type=int, default=50, help="Enforcement midpoint tick (default: 50)")
    parser.add_argument("--seed", type=int, default=42, help="Random seed (default: 42)")
    parser.add_argument("--compare", action="store_true", help="Run three scenarios side-by-side")
    parser.add_argument("--quiet", action="store_true", help="Suppress per-tick output")
    args = parser.parse_args()

    cfg = EcosystemConfig(
        n_species=args.species,
        ticks=args.ticks,
        dt=args.dt,
        enforcement_max=args.enforcement_max,
        enforcement_onset=args.enforcement_onset,
        seed=args.seed,
    )

    if args.compare:
        run_comparison(cfg)
    else:
        run_simulation(cfg, quiet=args.quiet)


if __name__ == "__main__":
    main()
