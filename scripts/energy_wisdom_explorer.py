# energy_wisdom_explorer.py

# Curiosity-Driven Energy System Exploration

# Weave heterogeneous energy practices into novel configurations

from dataclasses import dataclass, field
from typing import Dict, List, Any, Optional, Set, Tuple, Callable
from enum import Enum
from collections import defaultdict
import itertools
import math

# —————————

# Energy Practice Classification

# —————————

class EnergyOrigin(Enum):
“”“Origin classification for energy practices.”””
PIEZOELECTRIC = “piezoelectric”
THERMAL_MASS = “thermal_mass”
CONCENTRATED_SOLAR = “concentrated_solar”
THERMOELECTRIC = “thermoelectric”
BIOENERGY = “bioenergy”
WIND_PASSIVE = “wind_passive”
MAGNETIC = “magnetic”
RADIANT = “radiant”
GEOTHERMAL = “geothermal”
PHOTOVOLTAIC = “photovoltaic”
BIOMIMETIC = “biomimetic”
VERNACULAR = “vernacular”

class EnergyDomain(Enum):
“”“Domains of energy application.”””
GENERATION = “generation”
STORAGE = “storage”
TRANSMISSION = “transmission”
EFFICIENCY = “efficiency”
HEAT_MANAGEMENT = “heat_management”
MATERIALS = “materials”
MANUFACTURING = “manufacturing”
RECLAMATION = “reclamation”

# —————————

# Energy Practice

# —————————

@dataclass
class EnergyPractice:
“”“An energy practice with measurable parameters.”””
name: str
origin: EnergyOrigin
domains: List[EnergyDomain]
description: str
mechanism: str
parameters: Dict[str, float]
dependencies: List[str]
materials: List[str]
energy_return_on_investment: float    # EROI
scalability: float                    # 0-1
environment_fit: Dict[str, float] = field(default_factory=dict)
# environment_fit: tag → 0-1 suitability (e.g. “arid”: 0.9)

# —————————

# Practice Library

# —————————

class PracticeLibrary:
“””
Registry of energy practices.
Populate via register(); no hardcoded entries.
“””

```
def __init__(self):
    self.practices: Dict[str, EnergyPractice] = {}

def register(self, practice: EnergyPractice):
    self.practices[practice.name] = practice

def by_origin(self, origin: EnergyOrigin) -> List[EnergyPractice]:
    return [p for p in self.practices.values() if p.origin == origin]

def by_domain(self, domain: EnergyDomain) -> List[EnergyPractice]:
    return [p for p in self.practices.values() if domain in p.domains]

def by_environment(self, tag: str, threshold: float = 0.5) -> List[EnergyPractice]:
    """Practices suitable for a given environment tag above threshold."""
    return [
        p for p in self.practices.values()
        if p.environment_fit.get(tag, 0) >= threshold
    ]

def by_material(self, material: str) -> List[EnergyPractice]:
    return [p for p in self.practices.values() if material in p.materials]
```

# —————————

# Synergy Rule Engine

# —————————

@dataclass
class SynergyRule:
“”“A rule that detects synergy between two practices.”””
name: str
match_a: Callable[[EnergyPractice], bool]
match_b: Callable[[EnergyPractice], bool]
description: str
bonus: float = 0.1  # EROI multiplier bonus

class SynergyEngine:
“”“Detects synergies between practices using pluggable rules.”””

```
def __init__(self):
    self.rules: List[SynergyRule] = []

def add_rule(self, rule: SynergyRule):
    self.rules.append(rule)

def detect(
    self, practices: List[EnergyPractice]
) -> List[Dict[str, Any]]:
    """Find all synergies among a set of practices."""
    found = []
    for p1, p2 in itertools.combinations(practices, 2):
        for rule in self.rules:
            if (rule.match_a(p1) and rule.match_b(p2)) or \
               (rule.match_a(p2) and rule.match_b(p1)):
                found.append({
                    "rule": rule.name,
                    "practices": [p1.name, p2.name],
                    "description": rule.description,
                    "bonus": rule.bonus
                })
    return found
```

# —————————

# Energy System Weaver

# —————————

class EnergyWeaver:
“”“Weaves energy practices into integrated systems.”””

```
def __init__(
    self,
    library: PracticeLibrary,
    synergy_engine: Optional[SynergyEngine] = None
):
    self.library = library
    self.synergy_engine = synergy_engine or SynergyEngine()
    self.weavings: List[Dict[str, Any]] = []

def weave(
    self,
    practices: List[EnergyPractice],
    name: str
) -> Dict[str, Any]:
    """
    Weave practices into an integrated energy system.

    Returns
    -------
    dict with combined metrics, synergies, material list, domain coverage.
    """
    all_domains: Set[EnergyDomain] = set()
    all_materials: Set[str] = set()
    all_origins: Set[str] = set()

    for p in practices:
        all_domains.update(p.domains)
        all_materials.update(p.materials)
        all_origins.add(p.origin.value)

    # Synergy detection
    synergies = self.synergy_engine.detect(practices)
    synergy_bonus = sum(s["bonus"] for s in synergies)

    # Combined EROI (average + synergy)
    base_eroi = sum(p.energy_return_on_investment for p in practices) / len(practices)
    combined_eroi = base_eroi * (1 + synergy_bonus)

    # Environment fit (intersection across all practices)
    env_tags: Set[str] = set()
    for p in practices:
        env_tags.update(p.environment_fit.keys())
    env_scores = {}
    for tag in env_tags:
        scores = [p.environment_fit.get(tag, 0) for p in practices]
        env_scores[tag] = sum(scores) / len(scores)

    # Scalability (geometric mean)
    scalabilities = [p.scalability for p in practices if p.scalability > 0]
    combined_scalability = (
        math.prod(scalabilities) ** (1 / len(scalabilities))
        if scalabilities else 0
    )

    # Novelty: how many distinct origins
    novelty = len(all_origins) / max(1, len(practices))

    weaving = {
        "name": name,
        "practices": [p.name for p in practices],
        "origins": sorted(all_origins),
        "domains": sorted(d.value for d in all_domains),
        "materials": sorted(all_materials),
        "synergies": synergies,
        "combined_eroi": combined_eroi,
        "combined_scalability": combined_scalability,
        "environment_fit": env_scores,
        "novelty_score": novelty,
        "practice_count": len(practices),
        "domain_coverage": len(all_domains) / len(EnergyDomain),
    }

    self.weavings.append(weaving)
    return weaving

def weave_by_environment(
    self,
    tag: str,
    name: str,
    threshold: float = 0.5
) -> Dict[str, Any]:
    """Auto-select practices suited to an environment and weave them."""
    suited = self.library.by_environment(tag, threshold)
    if not suited:
        return {"name": name, "error": f"No practices found for '{tag}' ≥ {threshold}"}
    return self.weave(suited, name)

def weave_by_domain(
    self,
    domain: EnergyDomain,
    name: str
) -> Dict[str, Any]:
    """Auto-select practices covering a domain and weave them."""
    matching = self.library.by_domain(domain)
    if not matching:
        return {"name": name, "error": f"No practices found for domain '{domain.value}'"}
    return self.weave(matching, name)

def compare_weavings(self) -> List[Dict[str, Any]]:
    """Compare all weavings on key metrics."""
    return [
        {
            "name": w["name"],
            "eroi": w.get("combined_eroi", 0),
            "scalability": w.get("combined_scalability", 0),
            "novelty": w.get("novelty_score", 0),
            "domain_coverage": w.get("domain_coverage", 0),
            "synergy_count": len(w.get("synergies", [])),
        }
        for w in self.weavings
    ]
```
