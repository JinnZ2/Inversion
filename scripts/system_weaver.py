# system_weaver.py

# Curiosity-Driven System Exploration Engine

# Mix, match, and discover novel system configurations

from dataclasses import dataclass, field
from typing import Dict, List, Any, Optional, Tuple, Callable
from enum import Enum
from collections import defaultdict
import itertools
import random
import math

# —————————

# System Component Types

# —————————

class ComponentType(Enum):
“”“Swappable system component types.”””
WATER_SYSTEM = “water_system”
AIR_SYSTEM = “air_system”
DATA_SYSTEM = “data_system”
GENETIC_SYSTEM = “genetic_system”
ENERGY_SYSTEM = “energy_system”
KNOWLEDGE_SYSTEM = “knowledge_system”
SUPPLY_CHAIN = “supply_chain”
REGULATORY_FRAMEWORK = “regulatory_framework”
ECOLOGICAL_STRATEGY = “ecological_strategy”

@dataclass
class SystemComponent:
“”“A swappable system component.”””
name: str
type: ComponentType
description: str
parameters: Dict[str, float]
dependencies: Dict[str, float]       # dependency_name → intensity (0-1)
cost_structure: Dict[str, float]     # direct, hidden, externalized
emergent_properties: List[str] = field(default_factory=list)
origin: str = “”                     # classification tag

@dataclass
class SystemConfiguration:
“”“A complete system assembled from components.”””
name: str
components: Dict[ComponentType, SystemComponent]
coupling_strengths: Dict[Tuple[ComponentType, ComponentType], float]
performance_metrics: Dict[str, float] = field(default_factory=dict)
emergent_behaviors: List[str] = field(default_factory=list)

```
def calculate_metrics(self, calculator: 'SystemCalculator') -> Dict[str, float]:
    self.performance_metrics = calculator.calculate(self)
    return self.performance_metrics

def clone(self) -> 'SystemConfiguration':
    return SystemConfiguration(
        name=self.name + "_copy",
        components=dict(self.components),
        coupling_strengths=dict(self.coupling_strengths),
        performance_metrics=dict(self.performance_metrics),
        emergent_behaviors=list(self.emergent_behaviors)
    )
```

# —————————

# Component Library

# —————————

class ComponentLibrary:
“””
Registry of swappable components.
Populate via register() or load from external config.
“””

```
def __init__(self):
    self.components: Dict[ComponentType, List[SystemComponent]] = defaultdict(list)

def register(self, component: SystemComponent):
    """Add a component to the library."""
    self.components[component.type].append(component)

def get_options(self, comp_type: ComponentType) -> List[SystemComponent]:
    return self.components.get(comp_type, [])

def get_by_origin(self, origin: str) -> List[SystemComponent]:
    """All components with a given origin tag."""
    return [
        c for comps in self.components.values()
        for c in comps if c.origin == origin
    ]

def types_with_options(self) -> List[ComponentType]:
    """Component types that have at least one option registered."""
    return [t for t, comps in self.components.items() if comps]
```

# —————————

# System Calculator

# —————————

class SystemCalculator:
“”“Calculates system performance metrics from a configuration.”””

```
def __init__(self, coupling_origin_bonuses: Optional[Dict[str, float]] = None):
    """
    Parameters
    ----------
    coupling_origin_bonuses : dict, optional
        origin_tag → coupling bonus multiplier.
        When two components share an origin, this bonus applies.
    """
    self.coupling_origin_bonuses = coupling_origin_bonuses or {}

def calculate(self, config: SystemConfiguration) -> Dict[str, float]:
    metrics: Dict[str, float] = {}
    n = max(1, len(config.components))

    # Aggregate per-component parameters
    agg: Dict[str, float] = defaultdict(float)
    for comp in config.components.values():
        for key, val in comp.parameters.items():
            agg[key] += val
        agg["dependency_score"] += (
            sum(comp.dependencies.values()) / max(1, len(comp.dependencies))
        )
        agg["direct_cost"] += comp.cost_structure.get("direct", 0)
        agg["hidden_cost"] += comp.cost_structure.get("hidden", 0)

    # Normalize
    for key in list(agg):
        if key not in ("direct_cost", "hidden_cost"):
            agg[key] /= n

    metrics["dependency_score"] = agg["dependency_score"]
    metrics["total_cost"] = agg["direct_cost"]
    metrics["hidden_subsidy"] = agg["hidden_cost"]
    total = agg["direct_cost"] + agg["hidden_cost"]
    metrics["externalization_ratio"] = agg["hidden_cost"] / total if total > 0 else 0

    # Pass through averaged parameters
    for key in ("water_use", "carbon_impact", "biodiversity"):
        if key in agg:
            metrics[key] = agg[key]

    # Coupling synergy
    coupling_bonus = 0.0
    for (t1, t2), strength in config.coupling_strengths.items():
        if t1 in config.components and t2 in config.components:
            o1 = config.components[t1].origin
            o2 = config.components[t2].origin
            if o1 == o2 and o1 in self.coupling_origin_bonuses:
                coupling_bonus += strength * self.coupling_origin_bonuses[o1]

    metrics["coupling_synergy"] = coupling_bonus

    # Composite efficiency
    bio = metrics.get("biodiversity", 0)
    carbon = abs(metrics.get("carbon_impact", 0))
    dep = metrics.get("dependency_score", 0)
    ext = metrics.get("externalization_ratio", 0)
    syn = metrics.get("coupling_synergy", 0)

    metrics["system_efficiency"] = (
        bio * 0.3 +
        carbon * 0.2 +
        (1 - dep) * 0.2 +
        (1 - ext) * 0.2 +
        syn * 0.1
    )
    return metrics
```

# —————————

# Curiosity Explorer

# —————————

class CuriosityExplorer:
“”“Explores novel system combinations through mutation and recombination.”””

```
def __init__(self, library: ComponentLibrary, calculator: SystemCalculator):
    self.library = library
    self.calculator = calculator
    self.history: List[Dict] = []

def generate_random(self, name: str = "random") -> SystemConfiguration:
    """Generate a random configuration from the library."""
    components = {}
    for comp_type in self.library.types_with_options():
        options = self.library.get_options(comp_type)
        if options:
            components[comp_type] = random.choice(options)

    coupling = {}
    active_types = list(components.keys())
    for t1, t2 in itertools.combinations(active_types, 2):
        coupling[(t1, t2)] = random.uniform(0, 1)

    return SystemConfiguration(name, components, coupling)

def mutate(self, config: SystemConfiguration, rate: float = 0.3) -> SystemConfiguration:
    """Mutate a configuration by swapping components at given rate."""
    new = config.clone()
    for comp_type in list(new.components.keys()):
        if random.random() < rate:
            options = self.library.get_options(comp_type)
            current = new.components[comp_type]
            alts = [o for o in options if o.name != current.name]
            if alts:
                new.components[comp_type] = random.choice(alts)
    return new

def combine(
    self,
    a: SystemConfiguration,
    b: SystemConfiguration,
    name: str = "hybrid",
    selector: Optional[Callable[[SystemComponent, SystemComponent], SystemComponent]] = None
) -> SystemConfiguration:
    """
    Combine two configurations.

    Parameters
    ----------
    selector : callable, optional
        (comp_a, comp_b) → chosen_component.
        Defaults to random choice.
    """
    if selector is None:
        selector = lambda c1, c2: random.choice([c1, c2])

    combined_components = {}
    all_types = set(a.components) | set(b.components)
    for t in all_types:
        ca = a.components.get(t)
        cb = b.components.get(t)
        if ca and cb:
            combined_components[t] = selector(ca, cb)
        elif ca:
            combined_components[t] = ca
        elif cb:
            combined_components[t] = cb

    coupling = {}
    active = list(combined_components.keys())
    for t1, t2 in itertools.combinations(active, 2):
        s1 = a.coupling_strengths.get((t1, t2), 0)
        s2 = b.coupling_strengths.get((t1, t2), 0)
        coupling[(t1, t2)] = (s1 + s2) / 2

    return SystemConfiguration(name, combined_components, coupling)

def explore(
    self,
    base: SystemConfiguration,
    iterations: int = 100,
    mutation_rate: float = 0.4
) -> List[Tuple[SystemConfiguration, float]]:
    """
    Explore mutations around a base configuration.

    Returns
    -------
    list[(config, efficiency)] sorted best-first
    """
    results = []
    for i in range(iterations):
        candidate = self.mutate(base, rate=mutation_rate)
        metrics = candidate.calculate_metrics(self.calculator)
        eff = metrics.get("system_efficiency", 0)
        results.append((candidate, eff))
        self.history.append({
            "iteration": i,
            "efficiency": eff,
            "components": {t.value: c.name for t, c in candidate.components.items()}
        })
    results.sort(key=lambda x: -x[1])
    return results

def search_optimal(self, iterations: int = 500, refine_rate: float = 0.3) -> SystemConfiguration:
    """
    Search for optimal configuration via random generation + refinement.

    Returns best configuration found.
    """
    best: Optional[SystemConfiguration] = None
    best_eff = -1.0

    for i in range(iterations):
        if best and random.random() < refine_rate:
            candidate = self.mutate(best)
        else:
            candidate = self.generate_random(f"search_{i}")

        metrics = candidate.calculate_metrics(self.calculator)
        eff = metrics.get("system_efficiency", 0)

        if eff > best_eff:
            best_eff = eff
            best = candidate
            candidate.name = f"optimal_e{best_eff:.3f}"

    return best

def detect_emergent(
    self,
    config: SystemConfiguration,
    rules: Optional[List[Callable[[SystemConfiguration], Optional[str]]]] = None
) -> List[str]:
    """
    Detect emergent properties from component combinations.

    Parameters
    ----------
    rules : list[callable], optional
        Each rule takes a config and returns a description string or None.
        Defaults to built-in origin-counting heuristics.

    Returns
    -------
    list[str] — emergent property descriptions
    """
    emergent = []

    if rules:
        for rule in rules:
            result = rule(config)
            if result:
                emergent.append(result)
        return emergent

    # Default heuristics based on origin distribution
    origin_counts: Dict[str, int] = defaultdict(int)
    for comp in config.components.values():
        origin_counts[comp.origin] += 1

    n = len(config.components)
    if n == 0:
        return emergent

    # Dominant origin
    for origin, count in origin_counts.items():
        if count >= n * 0.75:
            emergent.append(f"Dominant-{origin} synergy: ≥75% components share origin")

    # Multi-origin hybrid
    if len(origin_counts) >= 3:
        emergent.append("Multi-paradigm hybrid: components drawn from 3+ origin classes")

    # Low dependency across all components
    dep_scores = [
        sum(c.dependencies.values()) / max(1, len(c.dependencies))
        for c in config.components.values()
    ]
    if dep_scores and all(d < 0.3 for d in dep_scores):
        emergent.append("System sovereignty: all components have low external dependency")

    return emergent
```
