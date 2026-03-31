# organization_topology.py

# Compare organizational topologies under explicit constraint sets

# Hierarchy vs Distributed vs Embedded-Rule (bee-like)

# No narrative — just mechanics

from dataclasses import dataclass, field
from typing import Dict, List, Any, Optional, Tuple
from enum import Enum
import math
import random

# —————————

# Topology Types

# —————————

class TopologyType(Enum):
HIERARCHY = “hierarchy”
DISTRIBUTED = “distributed”
EMBEDDED_RULE = “embedded_rule”

# —————————

# System Parameters

# —————————

@dataclass
class SystemParams:
“”“Parameters defining an organizational system.”””
name: str
topology: TopologyType
n_agents: int
update_rate: float              # compliance/coupling rate (α, β, or γ)
replacement_elasticity: float   # E_r: 0-1, how easily nodes swap without degradation
constraint_density: float       # D_c: constraints per node
externalization_capacity: float # S_e: 0-1, ability to push cost outside boundary
connectivity: int = 4           # k: neighbors per node (distributed only)

# —————————

# Simulation State

# —————————

@dataclass
class SimState:
“”“State of a running simulation.”””
positions: List[float]          # agent states x_i
target: float                   # T
time: int = 0
energy_spent: float = 0.0
history: List[float] = field(default_factory=list)  # E(t) over time

# —————————

# Topology Simulation Engine

# —————————

class TopologySimulator:
“””
Simulate convergence, energy, and failure for different topologies.

```
Update rules:
    Hierarchy:      x_i(t+1) = x_i + α * (u_parent - x_i)
    Distributed:    x_i(t+1) = x_i + β * Σ_neighbors(x_j - x_i)
    Embedded-rule:  x_i(t+1) = x_i + γ * ∇F(x_i, target)
"""

def __init__(self, params: SystemParams, target: float = 0.0, seed: int = 42):
    self.params = params
    self.rng = random.Random(seed)
    self.state = SimState(
        positions=[self.rng.gauss(0, 1) for _ in range(params.n_agents)],
        target=target,
    )
    self._build_topology()

def _build_topology(self):
    """Build adjacency structure based on topology type."""
    n = self.params.n_agents
    self.adjacency: Dict[int, List[int]] = {i: [] for i in range(n)}

    if self.params.topology == TopologyType.HIERARCHY:
        # Binary tree
        for i in range(n):
            parent = (i - 1) // 2 if i > 0 else None
            if parent is not None:
                self.adjacency[i].append(parent)
                self.adjacency[parent].append(i)

    elif self.params.topology == TopologyType.DISTRIBUTED:
        # Ring + random shortcuts
        k = self.params.connectivity
        for i in range(n):
            for j in range(1, k // 2 + 1):
                neighbor = (i + j) % n
                if neighbor not in self.adjacency[i]:
                    self.adjacency[i].append(neighbor)
                    self.adjacency[neighbor].append(i)

    elif self.params.topology == TopologyType.EMBEDDED_RULE:
        # No explicit adjacency — each node uses local gradient
        pass

def error(self) -> float:
    """Total squared error E(t) = Σ(x_i - T)²."""
    return sum((x - self.state.target) ** 2 for x in self.state.positions)

def step(self):
    """One simulation step."""
    n = self.params.n_agents
    α = self.params.update_rate
    new_positions = list(self.state.positions)
    step_energy = 0.0

    if self.params.topology == TopologyType.HIERARCHY:
        # Top-down: node 0 is root, knows target
        # Information compresses at each level
        for i in range(n):
            if i == 0:
                command = self.state.target
            else:
                parent = (i - 1) // 2
                # Parent's signal, with compression noise
                depth = int(math.log2(i + 1))
                noise = self.rng.gauss(0, 0.05 * depth)
                command = self.state.positions[parent] + noise

            delta = α * (command - self.state.positions[i])
            new_positions[i] = self.state.positions[i] + delta
            step_energy += abs(delta)

    elif self.params.topology == TopologyType.DISTRIBUTED:
        for i in range(n):
            neighbors = self.adjacency[i]
            if not neighbors:
                continue
            avg_neighbor = sum(self.state.positions[j] for j in neighbors) / len(neighbors)
            delta = α * (avg_neighbor - self.state.positions[i])
            new_positions[i] = self.state.positions[i] + delta
            step_energy += abs(delta)

    elif self.params.topology == TopologyType.EMBEDDED_RULE:
        # Each node independently moves toward target via local gradient
        for i in range(n):
            gradient = self.state.target - self.state.positions[i]
            delta = α * gradient
            new_positions[i] = self.state.positions[i] + delta
            step_energy += abs(delta)

    # Apply externalization: fraction of energy "exported" (not counted)
    visible_energy = step_energy * (1 - self.params.externalization_capacity)

    self.state.positions = new_positions
    self.state.time += 1
    self.state.energy_spent += visible_energy
    self.state.history.append(self.error())

def perturb(self, fraction: float = 0.3, sigma: float = 2.0):
    """Randomly displace a fraction of agents."""
    n = self.params.n_agents
    count = max(1, int(n * fraction))
    indices = self.rng.sample(range(n), count)
    for i in indices:
        self.state.positions[i] += self.rng.gauss(0, sigma)

def remove_nodes(self, fraction: float = 0.05):
    """Remove a fraction of nodes (simulate failure)."""
    n = len(self.state.positions)
    count = max(1, int(n * fraction))
    indices = sorted(self.rng.sample(range(n), count), reverse=True)
    for i in indices:
        self.state.positions.pop(i)
    self.params.n_agents = len(self.state.positions)
    self._build_topology()

def run(self, steps: int = 100) -> Dict[str, Any]:
    """Run simulation and return results."""
    for _ in range(steps):
        self.step()

    return self.results()

def results(self) -> Dict[str, Any]:
    """Current simulation results."""
    # Convergence: first time error drops below threshold
    threshold = 0.1 * self.params.n_agents
    convergence_time = None
    for t, e in enumerate(self.state.history):
        if e < threshold:
            convergence_time = t
            break

    return {
        "name": self.params.name,
        "topology": self.params.topology.value,
        "n_agents": self.params.n_agents,
        "final_error": self.error(),
        "convergence_time": convergence_time,
        "total_energy": self.state.energy_spent,
        "externalization": self.params.externalization_capacity,
        "steps_run": self.state.time,
        "error_history": self.state.history,
    }
```

# —————————

# Comparative Analysis

# —————————

def compare_topologies(
n_agents: int = 64,
steps: int = 100,
externalization: float = 0.0,
perturbation_at: Optional[int] = None,
failure_at: Optional[int] = None,
seed: int = 42,
) -> List[Dict[str, Any]]:
“””
Run all three topologies under identical conditions and compare.

```
Parameters
----------
n_agents : int
steps : int
externalization : float
    S_e for all systems (set to 0 for closed-loop comparison)
perturbation_at : int, optional
    Step at which to inject perturbation
failure_at : int, optional
    Step at which to remove 5% of nodes
seed : int

Returns
-------
list of result dicts, one per topology
"""
configs = [
    SystemParams("Hierarchy", TopologyType.HIERARCHY, n_agents, 0.5,
                  replacement_elasticity=0.9, constraint_density=0.6,
                  externalization_capacity=externalization),
    SystemParams("Distributed", TopologyType.DISTRIBUTED, n_agents, 0.3,
                  replacement_elasticity=0.7, constraint_density=0.3,
                  externalization_capacity=externalization, connectivity=4),
    SystemParams("Embedded-Rule", TopologyType.EMBEDDED_RULE, n_agents, 0.4,
                  replacement_elasticity=0.5, constraint_density=0.1,
                  externalization_capacity=externalization),
]

results = []
for cfg in configs:
    sim = TopologySimulator(cfg, target=0.0, seed=seed)
    for t in range(steps):
        if perturbation_at is not None and t == perturbation_at:
            sim.perturb()
        if failure_at is not None and t == failure_at:
            sim.remove_nodes()
        sim.step()
    results.append(sim.results())

return results
```
