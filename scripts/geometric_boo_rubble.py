# geometric_boo_rubble.py

# Base of Operations from salvaged/local materials

# Generic framework: populate material and component registries, then design

from dataclasses import dataclass, field
from typing import Dict, List, Any, Optional, Callable
import math

# —————————

# Salvaged Material

# —————————

@dataclass
class SalvagedMaterial:
“”“A material recoverable from the environment or debris.”””
name: str
source: str
properties: List[str]
applications: List[str]
availability: float          # 0-1, how common
energy_to_process: float     # kWh/kg
safety_concerns: List[str] = field(default_factory=list)

# —————————

# Salvage Component

# —————————

@dataclass
class SalvageComponent:
“”“A system component built from salvaged materials.”””
name: str
function: str
materials: List[str]         # material names required
tools: List[str]             # basic tools needed
output_w: float              # watts (if power)
output_l_per_day: float      # liters/day (if water)
build_time_hours: float
lifespan_years: float
difficulty: float            # 1-5
tags: Dict[str, str] = field(default_factory=dict)

# —————————

# Coupling Rule

# —————————

@dataclass
class CouplingRule:
“”“Detects a coupling between two salvage components.”””
name: str
requires: List[str]
description: str
strength: float = 0.7

# —————————

# Material Library

# —————————

class MaterialLibrary:
“”“Registry of salvageable materials. Populate via register().”””

```
def __init__(self):
    self.materials: Dict[str, SalvagedMaterial] = {}

def register(self, material: SalvagedMaterial):
    self.materials[material.name] = material

def available(self, threshold: float = 0.3) -> List[SalvagedMaterial]:
    return [m for m in self.materials.values() if m.availability >= threshold]

def by_property(self, prop: str) -> List[SalvagedMaterial]:
    return [m for m in self.materials.values() if prop in m.properties]
```

# —————————

# Component Library

# —————————

class SalvageComponentLibrary:
“”“Registry of components buildable from salvaged materials.”””

```
def __init__(self):
    self.components: Dict[str, SalvageComponent] = {}

def register(self, component: SalvageComponent):
    self.components[component.name] = component

def all(self) -> List[SalvageComponent]:
    return list(self.components.values())

def by_function(self, function_keyword: str) -> List[SalvageComponent]:
    return [
        c for c in self.components.values()
        if function_keyword.lower() in c.function.lower()
    ]
```

# —————————

# Salvage BOO Designer

# —————————

class SalvageBOO:
“””
Design a BOO from salvaged materials.
Selects components based on material availability,
identifies couplings, computes geometric metrics.
“””

```
def __init__(
    self,
    material_library: MaterialLibrary,
    component_library: SalvageComponentLibrary,
    coupling_rules: Optional[List[CouplingRule]] = None,
    water_per_person_l: float = 15.0,
    power_per_person_w: float = 100.0,
):
    self.materials = material_library
    self.components = component_library
    self.coupling_rules = coupling_rules or []
    self.water_per_person_l = water_per_person_l
    self.power_per_person_w = power_per_person_w

def feasible_components(
    self,
    available_materials: Dict[str, float],
    threshold: float = 0.3,
) -> List[str]:
    """
    Components whose required materials are all available above threshold.
    """
    feasible = []
    for name, comp in self.components.components.items():
        if all(
            available_materials.get(mat, 0) >= threshold
            for mat in comp.materials
        ):
            feasible.append(name)
    return feasible

def identify_couplings(self, selected: List[str]) -> List[Dict[str, Any]]:
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
    n = len(selected)
    nc = len(couplings)
    max_c = n * (n - 1) / 2 if n > 1 else 1
    density = nc / max_c if max_c > 0 else 0
    avg_str = sum(c.get("strength", 0) for c in couplings) / nc if nc else 0
    area = n * density * avg_str
    return {
        "vectors": n,
        "couplings": nc,
        "coupling_density": density,
        "avg_coupling_strength": avg_str,
        "geometric_area": area,
        "integrity": min(1.0, area / 10),
    }

def design(
    self,
    population: int,
    available_materials: Dict[str, float],
    threshold: float = 0.3,
) -> Dict[str, Any]:
    """Full system design from available materials."""
    target_water = population * self.water_per_person_l
    target_power = population * self.power_per_person_w

    selected = self.feasible_components(available_materials, threshold)
    couplings = self.identify_couplings(selected)

    total_water = sum(
        self.components.components[n].output_l_per_day
        for n in selected if n in self.components.components
    )
    total_power = sum(
        self.components.components[n].output_w
        for n in selected if n in self.components.components
    )
    total_build = sum(
        self.components.components[n].build_time_hours
        for n in selected if n in self.components.components
    )

    multiplier = 1
    if total_water > 0:
        multiplier = max(multiplier, math.ceil(target_water / total_water))
    if total_power > 0:
        multiplier = max(multiplier, math.ceil(target_power / total_power))

    metrics = self.geometric_metrics(selected, couplings)

    all_mats = sorted(set(
        mat
        for n in selected if n in self.components.components
        for mat in self.components.components[n].materials
    ))

    return {
        "population": population,
        "target_water_l_day": target_water,
        "target_power_w": target_power,
        "selected_components": selected,
        "multiplier": multiplier,
        "total_water_l_day": total_water * multiplier,
        "total_power_w": total_power * multiplier,
        "total_build_time_hours": total_build * multiplier,
        "materials_used": all_mats,
        "couplings": couplings,
        "geometric_metrics": metrics,
    }
```
