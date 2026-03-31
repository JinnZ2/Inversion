# desert_sand_energy_coupling.py

# Physics framework for multi-domain energy coupling from substrate materials

# Generic: populate with domain-specific couplings via register()

import math
import itertools
from dataclasses import dataclass, field
from typing import Dict, List, Any, Optional, Tuple, Callable
from enum import Enum
from collections import defaultdict

# —————————

# Physics Domains

# —————————

class PhysicsDomain(Enum):
“”“Physics domains available for coupling.”””
MECHANICAL = “mechanical”
THERMAL = “thermal”
ELECTROMAGNETIC = “electromagnetic”
QUANTUM = “quantum”
ACOUSTIC = “acoustic”
OPTICAL = “optical”
CHEMICAL = “chemical”
GRAVITATIONAL = “gravitational”
FLUID_DYNAMIC = “fluid_dynamic”
THERMOELECTRIC = “thermoelectric”
PIEZOELECTRIC = “piezoelectric”
PYROELECTRIC = “pyroelectric”
TRIBOELECTRIC = “triboelectric”
MAGNETIC = “magnetic”
RADIO_FREQUENCY = “radio_frequency”

@dataclass
class EnergyCoupling:
“”“A coupling technique to extract energy from a substrate.”””
name: str
physics: List[PhysicsDomain]
mechanism: str
efficiency: float               # 0-1
power_density: Optional[float]  # W/m² or W/kg (None if enhancement-only)
scalability: float              # 0-1
environment_fit: Dict[str, float] = field(default_factory=dict)
# environment tag → 0-1 suitability
resonance_frequency: Optional[float] = None  # Hz, if resonant
materials_needed: List[str] = field(default_factory=list)
status: str = “”

# —————————

# Coupling Library

# —————————

class CouplingLibrary:
“”“Registry of energy coupling techniques. Populate via register().”””

```
def __init__(self):
    self.couplings: Dict[str, EnergyCoupling] = {}

def register(self, coupling: EnergyCoupling):
    self.couplings[coupling.name] = coupling

def all(self) -> List[EnergyCoupling]:
    return list(self.couplings.values())

def by_physics(self, domain: PhysicsDomain) -> List[EnergyCoupling]:
    return [c for c in self.couplings.values() if domain in c.physics]

def by_environment(self, tag: str, threshold: float = 0.5) -> List[EnergyCoupling]:
    return [
        c for c in self.couplings.values()
        if c.environment_fit.get(tag, 0) >= threshold
    ]

def by_scalability(self, minimum: float) -> List[EnergyCoupling]:
    return [c for c in self.couplings.values() if c.scalability >= minimum]

def resonant(self) -> List[EnergyCoupling]:
    return [c for c in self.couplings.values() if c.resonance_frequency is not None]

def by_material(self, material: str) -> List[EnergyCoupling]:
    return [c for c in self.couplings.values() if material in c.materials_needed]
```

# —————————

# Synergy Rule Engine

# —————————

@dataclass
class SynergyRule:
“”“Pluggable rule for detecting synergy between two couplings.”””
name: str
match_a: Callable[[EnergyCoupling], bool]
match_b: Callable[[EnergyCoupling], bool]
description: str
bonus: float = 0.1  # additive power-density or EROI bonus factor

class SynergyEngine:
“”“Detects synergies via pluggable rules.”””

```
def __init__(self):
    self.rules: List[SynergyRule] = []

def add_rule(self, rule: SynergyRule):
    self.rules.append(rule)

def detect(self, couplings: List[EnergyCoupling]) -> List[Dict[str, Any]]:
    found = []
    for c1, c2 in itertools.combinations(couplings, 2):
        for rule in self.rules:
            if (rule.match_a(c1) and rule.match_b(c2)) or \
               (rule.match_a(c2) and rule.match_b(c1)):
                found.append({
                    "rule": rule.name,
                    "couplings": [c1.name, c2.name],
                    "description": rule.description,
                    "bonus": rule.bonus,
                })
    return found
```

# —————————

# Coupling Weaver

# —————————

class CouplingWeaver:
“”“Weaves coupling techniques into integrated energy systems.”””

```
def __init__(
    self,
    library: CouplingLibrary,
    synergy_engine: Optional[SynergyEngine] = None,
):
    self.library = library
    self.synergy_engine = synergy_engine or SynergyEngine()
    self.weavings: List[Dict[str, Any]] = []

def weave(
    self, couplings: List[EnergyCoupling], name: str
) -> Dict[str, Any]:
    """Weave couplings into an integrated system."""

    all_physics: set = set()
    all_materials: set = set()
    power_sources: List[float] = []

    for c in couplings:
        all_physics.update(c.physics)
        all_materials.update(c.materials_needed)
        if c.power_density is not None:
            power_sources.append(c.power_density)

    synergies = self.synergy_engine.detect(couplings)
    synergy_bonus = sum(s["bonus"] for s in synergies)

    total_power = sum(power_sources)
    avg_efficiency = (
        sum(c.efficiency for c in couplings) / len(couplings)
        if couplings else 0
    )
    avg_scalability = (
        sum(c.scalability for c in couplings) / len(couplings)
        if couplings else 0
    )

    # Environment fit intersection
    env_tags: set = set()
    for c in couplings:
        env_tags.update(c.environment_fit.keys())
    env_scores = {}
    for tag in env_tags:
        scores = [c.environment_fit.get(tag, 0) for c in couplings]
        env_scores[tag] = sum(scores) / len(scores)

    # Resonance spectrum
    resonant = [c for c in couplings if c.resonance_frequency is not None]
    freq_bands = sorted(set(c.resonance_frequency for c in resonant))

    # Novel coupling detection
    novel: List[str] = []
    if len(all_physics) >= 5:
        novel.append(
            f"Multi-physics harvesting: {len(all_physics)} domains coupled"
        )
    if len(freq_bands) >= 2:
        novel.append(
            f"Multi-resonant system: {len(freq_bands)} frequency bands"
        )

    weaving = {
        "name": name,
        "couplings": [c.name for c in couplings],
        "physics_domains": sorted(p.value for p in all_physics),
        "materials": sorted(all_materials),
        "synergies": synergies,
        "novel_couplings": novel,
        "total_power_density": total_power,
        "average_efficiency": avg_efficiency,
        "average_scalability": avg_scalability,
        "environment_fit": env_scores,
        "frequency_bands": freq_bands,
    }

    self.weavings.append(weaving)
    return weaving

def weave_by_environment(
    self, tag: str, name: str, threshold: float = 0.5
) -> Dict[str, Any]:
    suited = self.library.by_environment(tag, threshold)
    if not suited:
        return {"name": name, "error": f"No couplings for '{tag}' ≥ {threshold}"}
    return self.weave(suited, name)

def weave_by_physics(
    self, domain: PhysicsDomain, name: str
) -> Dict[str, Any]:
    matching = self.library.by_physics(domain)
    if not matching:
        return {"name": name, "error": f"No couplings for '{domain.value}'"}
    return self.weave(matching, name)

def weave_resonant(self, name: str = "Resonant System") -> Dict[str, Any]:
    resonant = self.library.resonant()
    if not resonant:
        return {"name": name, "error": "No resonant couplings registered"}
    return self.weave(resonant, name)

def compare_weavings(self) -> List[Dict[str, Any]]:
    return [
        {
            "name": w["name"],
            "power": w.get("total_power_density", 0),
            "efficiency": w.get("average_efficiency", 0),
            "scalability": w.get("average_scalability", 0),
            "physics_count": len(w.get("physics_domains", [])),
            "synergy_count": len(w.get("synergies", [])),
        }
        for w in self.weavings
    ]
```
