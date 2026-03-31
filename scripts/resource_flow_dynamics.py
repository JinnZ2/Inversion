# resource_flow_dynamics.py

# Coupled resource flow dynamics: accumulation vs circulation vs coupling

# Single-pool and multi-agent networked versions

# Configurable parameters, no domain-specific framing

import numpy as np
from dataclasses import dataclass, field
from typing import Dict, List, Any, Optional, Tuple

# —————————

# Single-Pool Model

# —————————

@dataclass
class FlowParams:
“”“Parameters for single-pool H/C/R dynamics.”””
alpha: float = 0.08    # extraction rate (C → H)
beta: float = 0.02     # release rate (H → C)
delta: float = 0.04    # productivity (C generates more C)
gamma: float = 0.02    # dissipation (entropy loss from C)
k1: float = 0.005      # responsiveness degradation rate
k2: float = 0.010      # responsiveness recovery rate
C_ref: float = 100.0   # reference C level for signal normalization
dt: float = 0.1        # time step

@dataclass
class FlowState:
“”“State of a single-pool system.”””
C: float = 100.0       # circulating resource
H: float = 10.0        # hoarded/stored resource
R: float = 1.0         # responsiveness (coupling efficiency, 0-1)

def step_single(state: FlowState, params: FlowParams) -> FlowState:
“”“Advance single-pool system by one time step.”””
C, H, R = state.C, state.H, state.R
dt = params.dt

```
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
    R=np.clip(R + dR * dt, 0, 1),
)
```

def run_single(
params: FlowParams,
initial: Optional[FlowState] = None,
steps: int = 2000,
) -> Dict[str, Any]:
“””
Run single-pool simulation.

```
Returns
-------
dict with time series for C, H, R, throughput, and total resource.
"""
state = initial or FlowState()
history = {"C": [], "H": [], "R": [], "throughput": [], "total": []}

for _ in range(steps):
    throughput = params.delta * state.C * state.R
    history["C"].append(state.C)
    history["H"].append(state.H)
    history["R"].append(state.R)
    history["throughput"].append(throughput)
    history["total"].append(state.C + state.H)
    state = step_single(state, params)

return {k: np.array(v) for k, v in history.items()}
```

# —————————

# Multi-Agent Networked Model

# —————————

@dataclass
class NetworkParams:
“”“Parameters for multi-agent networked dynamics.”””
n_agents: int = 30
kappa: float = 0.15          # network flow strength
alpha: Optional[np.ndarray] = None   # per-agent extraction rates
beta: Optional[np.ndarray] = None    # per-agent release rates
delta: Optional[np.ndarray] = None   # per-agent productivity
gamma: Optional[np.ndarray] = None   # per-agent dissipation
k1: float = 0.004            # responsiveness degradation
k2: float = 0.008            # responsiveness recovery
C_ref: float = 50.0          # reference C level for signal normalization
dt: float = 0.05
adjacency: Optional[np.ndarray] = None  # row-stochastic adjacency matrix

```
def __post_init__(self):
    n = self.n_agents
    if self.alpha is None:
        self.alpha = np.full(n, 0.06)
    if self.beta is None:
        self.beta = np.full(n, 0.02)
    if self.delta is None:
        self.delta = np.full(n, 0.04)
    if self.gamma is None:
        self.gamma = np.full(n, 0.02)
    if self.adjacency is None:
        A = np.random.rand(n, n)
        A = A / A.sum(axis=1, keepdims=True)
        np.fill_diagonal(A, 0.0)
        self.adjacency = A
```

@dataclass
class NetworkState:
“”“State of a multi-agent network.”””
C: np.ndarray   # circulating per agent
H: np.ndarray   # stored per agent
R: np.ndarray   # responsiveness per agent

```
@classmethod
def default(cls, n: int, seed: int = 42) -> "NetworkState":
    rng = np.random.RandomState(seed)
    return cls(
        C=np.clip(50 + 10 * rng.randn(n), 10, None),
        H=10 * np.ones(n),
        R=np.ones(n),
    )
```

def network_flow(C: np.ndarray, A: np.ndarray, kappa: float) -> np.ndarray:
“”“Compute net flow for each agent from diffusion on adjacency.”””
Ci = C.reshape(-1, 1)
Cj = C.reshape(1, -1)
F = kappa * A * (Ci - Cj)
return F.T.sum(axis=1) - F.sum(axis=1)

def step_network(state: NetworkState, params: NetworkParams) -> NetworkState:
“”“Advance network by one time step.”””
C, H, R = state.C, state.H, state.R
dt = params.dt

```
extraction = params.alpha * C
release = params.beta * H
productivity = params.delta * C * R
dissipation = params.gamma * C
net_flow = network_flow(C, params.adjacency, params.kappa)
signal = C / params.C_ref

dC = -extraction + release + productivity - dissipation + net_flow
dH = extraction - release
dR = -params.k1 * signal + params.k2 * (1.0 - R)

return NetworkState(
    C=np.clip(C + dC * dt, 0, None),
    H=np.clip(H + dH * dt, 0, None),
    R=np.clip(R + dR * dt, 0, 1),
)
```

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
“””
Run multi-agent network simulation.

```
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
rng = np.random.RandomState(seed)

# Apply hoarder parameters
if hoarder_indices:
    for i in hoarder_indices:
        params.alpha[i] = hoarder_alpha
        params.beta[i] = hoarder_beta

state = initial or NetworkState.default(params.n_agents, seed)

agg = {
    "total_C": [], "total_H": [], "total_throughput": [],
    "mean_R": [], "min_R": [],
}

for t in range(steps):
    # Perturbation
    if perturbation_step is not None and t == perturbation_step:
        count = max(1, int(params.n_agents * perturbation_fraction))
        indices = rng.choice(params.n_agents, count, replace=False)
        state.C[indices] += rng.normal(0, perturbation_sigma, count)
        state.C = np.clip(state.C, 0, None)

    throughput = params.delta * state.C * state.R

    agg["total_C"].append(state.C.sum())
    agg["total_H"].append(state.H.sum())
    agg["total_throughput"].append(throughput.sum())
    agg["mean_R"].append(state.R.mean())
    agg["min_R"].append(state.R.min())

    state = step_network(state, params)

return {
    "aggregates": {k: np.array(v) for k, v in agg.items()},
    "final_state": {
        "C": state.C.copy(),
        "H": state.H.copy(),
        "R": state.R.copy(),
    },
    "params": {
        "n_agents": params.n_agents,
        "kappa": params.kappa,
        "k1": params.k1,
        "k2": params.k2,
        "hoarder_indices": hoarder_indices or [],
    },
}
```

# —————————

# Analysis Utilities

# —————————

def diagnose_single(history: Dict[str, np.ndarray]) -> Dict[str, Any]:
“”“Diagnose single-pool run.”””
C, H, R = history[“C”], history[“H”], history[“R”]
tp = history[“throughput”]

```
peak_throughput_t = int(np.argmax(tp))
final_R = float(R[-1])
total_accumulated = float(H[-1])
total_circulating = float(C[-1])

# Detect collapse: throughput drops below 20% of peak
peak_tp = tp.max()
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
```

def diagnose_network(result: Dict[str, Any]) -> Dict[str, Any]:
“”“Diagnose network run.”””
agg = result[“aggregates”]
tp = agg[“total_throughput”]
mean_R = agg[“mean_R”]

```
peak_tp = float(tp.max())
peak_t = int(np.argmax(tp))
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
```

def _gini(arr: np.ndarray) -> float:
“”“Gini coefficient (0 = equal, 1 = one agent has everything).”””
arr = np.abs(arr)
if arr.sum() == 0:
return 0.0
sorted_arr = np.sort(arr)
n = len(sorted_arr)
index = np.arange(1, n + 1)
return float((2 * (index * sorted_arr).sum() / (n * sorted_arr.sum())) - (n + 1) / n)
