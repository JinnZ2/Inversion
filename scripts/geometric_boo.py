# geometric_boo.py

# Base of Operations: Distributed infrastructure systems

# Geometric principles: multiple vectors, coupled, no single point of failure

from dataclasses import dataclass, field
from typing import Dict, List, Any, Optional, Tuple, Callable
from enum import Enum
import math

# —————————

# BOO Component

# —————————

@dataclass
class BOOComponent:
“”“A modular infrastructure component.”””
name: str
function: str
mass_kg: float
volume_m3: float
power_w: float               # watts generated (negative = consumed)
water_l_per_day: float       # liters/day produced
cost_usd: float
deployment_time_hours: float
lifespan_years: float
dependencies: List[str]      # what it needs to operate
provides: List[str]          # what it outputs
tags: Dict[str, str] = field(default_factory=dict)

# —————————

# Coupling Rule

# —————————

@dataclass
class CouplingRule:
“”“Detects a coupling between two components.”””
name: str
requires: List[str]           # component names that must all be present
description: str
strength: float = 0.7

# —————————

# Component Library

# —————————

class BOOComponentLibrary:
“”“Registry of BOO components. Populate via register().”””

```
def __init__(self):
    self.components: Dict[str, BOOComponent] = {}

def register(self, component: BOOComponent):
    self.components[component.name] = component

def by_provides(self, resource: str) -> List[BOOComponent]:
    return [c for c in self.components.values() if resource in c.provides]

def by_dependency(self, dep: str) -> List[BOOComponent]:
    return [c for c in self.components.values() if dep in c.dependencies]

def all(self) -> List[BOOComponent]:
    return list(self.components.values())
```

# —————————

# Geometric BOO

# —————————

class GeometricBOO:
“””
Distributed, coupled infrastructure system.
Selects components based on context, computes geometric metrics.
“””

```
def __init__(
    self,
    library: BOOComponentLibrary,
    coupling_rules: Optional[List[CouplingRule]] = None,
    water_per_person_l: float = 15.0,
    power_per_person_w: float = 100.0,
):
    self.library = library
    self.coupling_rules = coupling_rules or []
    self.water_per_person_l = water_per_person_l
    self.power_per_person_w = power_per_person_w

def requirements(self, population: int) -> Dict[str, float]:
    return {
        "population": population,
        "water_l_per_day": population * self.water_per_person_l,
        "power_w": population * self.power_per_person_w,
    }

def select_components(
    self,
    context: Dict[str, Any],
    selector: Optional[Callable[[BOOComponent, Dict], bool]] = None,
) -> List[str]:
    """
    Select components suitable for context.

    Parameters
    ----------
    context : dict
        Available resources / conditions (e.g. sunlight, wind, groundwater).
    selector : callable, optional
        (component, context) → bool. Defaults to dependency check.

    Returns
    -------
    list of component names
    """
    if selector is None:
        def selector(comp, ctx):
            return all(
                ctx.get(dep, False)
                for dep in comp.dependencies
                if dep not in ("human_power", "gravity", "elevation_difference")
            )

    return [
        name for name, comp in self.library.components.items()
        if selector(comp, context)
    ]

def identify_couplings(self, selected: List[str]) -> List[Dict[str, Any]]:
    """Find active coupling rules for selected components."""
    active = []
    for rule in self.coupling_rules:
        if all(r in selected for r in rule.requires):
            active.append({
                "components": rule.requires,
                "description": rule.description,
                "strength": rule.strength,
            })
    return active

def geometric_metrics(
    self, selected: List[str], couplings: List[Dict]
) -> Dict[str, float]:
    """Compute geometric integrity metrics."""
    n = len(selected)
    nc = len(couplings)
    max_c = n * (n - 1) / 2 if n > 1 else 1
    density = nc / max_c if max_c > 0 else 0
    avg_str = (
        sum(c.get("strength", 0) for c in couplings) / nc if nc > 0 else 0
    )
    area = n * density * avg_str
    integrity = min(1.0, area / 10)
    return {
        "vectors": n,
        "couplings": nc,
        "coupling_density": density,
        "avg_coupling_strength": avg_str,
        "geometric_area": area,
        "integrity": integrity,
    }

def design(
    self,
    population: int,
    context: Dict[str, Any],
    selector: Optional[Callable] = None,
) -> Dict[str, Any]:
    """
    Full system design.

    Returns
    -------
    dict with requirements, selected components, capacity, couplings, metrics.
    """
    reqs = self.requirements(population)
    selected = self.select_components(context, selector)
    couplings = self.identify_couplings(selected)

    total_power = sum(
        self.library.components[n].power_w
        for n in selected if n in self.library.components
    )
    total_water = sum(
        self.library.components[n].water_l_per_day
        for n in selected if n in self.library.components
    )

    multiplier = 1
    if total_power > 0:
        multiplier = max(multiplier, math.ceil(reqs["power_w"] / total_power))
    if total_water > 0:
        multiplier = max(multiplier, math.ceil(reqs["water_l_per_day"] / total_water))

    total_cost = sum(
        self.library.components[n].cost_usd
        for n in selected if n in self.library.components
    ) * multiplier

    deploy_time = max(
        (self.library.components[n].deployment_time_hours
         for n in selected if n in self.library.components),
        default=0,
    ) * multiplier

    metrics = self.geometric_metrics(selected, couplings)

    return {
        "requirements": reqs,
        "context": context,
        "selected_components": selected,
        "multiplier": multiplier,
        "total_power_w": total_power * multiplier,
        "total_water_l_per_day": total_water * multiplier,
        "total_cost_usd": total_cost,
        "deployment_time_hours": deploy_time,
        "couplings": couplings,
        "geometric_metrics": metrics,
    }
```
