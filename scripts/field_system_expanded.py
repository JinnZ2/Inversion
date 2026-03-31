# field_system_expanded.py

# Full dependency accounting for agricultural systems

# Framework for internalizing externalized costs

from dataclasses import dataclass, field
from typing import Dict, Any, List, Optional
from enum import Enum
import math

# —————————

# Dependency Classification

# —————————

class DependencyType(Enum):
“”“Types of dependencies that production systems may externalize.”””
CLEAN_WATER = “clean_water”
CLEAN_AIR = “clean_air”
DATA_INFRASTRUCTURE = “data_infrastructure”
SATELLITE_SYSTEMS = “satellite_systems”
PROPRIETARY_SOFTWARE = “proprietary_software”
GENETIC_IP = “genetic_ip”
SUPPLY_CHAIN = “supply_chain”
REGULATORY_COMPLIANCE = “regulatory_compliance”

@dataclass
class Dependency:
“”“A dependency that a production system may externalize.”””
name: str
type: DependencyType
current_cost: float          # Apparent cost (unit/time)
hidden_subsidy: float        # Externalized cost (unit/time)
degradation_rate: float      # Rate of depletion (+) or regeneration (-)
alternative_cost: float      # Cost of internalized alternative
measurement_method: str

```
def true_cost(self) -> float:
    """True cost including externalized subsidies."""
    return self.current_cost + self.hidden_subsidy

def sustainability_index(self) -> float:
    """0-1, how sustainable current usage is."""
    return max(0, 1 - self.degradation_rate)
```

# —————————

# Expanded Field System

# —————————

class ExpandedFieldSystem:
“””
Production system with full dependency accounting.
Treats shared resources as depletable inputs.
“””

```
def __init__(self):
    self.dependencies: Dict[str, Dependency] = {}
    self.production_metrics: Dict[str, float] = {}
    self.ecological_metrics: Dict[str, float] = {}

def register_dependency(self, dependency: Dependency):
    self.dependencies[dependency.name] = dependency

def set_production_metrics(self, metrics: Dict[str, float]):
    self.production_metrics = metrics

def set_ecological_metrics(self, metrics: Dict[str, float]):
    self.ecological_metrics = metrics

def total_dependency_cost(self) -> Dict[str, Any]:
    """Calculate total cost of dependencies including externalities."""
    total = 0
    hidden_total = 0
    details = {}

    for name, dep in self.dependencies.items():
        true_cost = dep.true_cost()
        hidden = dep.hidden_subsidy
        total += true_cost
        hidden_total += hidden

        details[name] = {
            "type": dep.type.value,
            "apparent_cost": dep.current_cost,
            "hidden_subsidy": hidden,
            "true_cost": true_cost,
            "degradation_rate": dep.degradation_rate,
            "sustainability": dep.sustainability_index()
        }

    return {
        "total_true_cost": total,
        "total_hidden_subsidy": hidden_total,
        "externalization_ratio": hidden_total / total if total > 0 else 0,
        "details": details
    }

def true_system_efficiency(self) -> float:
    """
    Efficiency accounting for all dependencies.
    yield / (apparent_inputs + true_dependency_costs) * avg_sustainability
    """
    yield_value = self.production_metrics.get("output_yield", 0)
    apparent_inputs = self.production_metrics.get("input_energy", 1)

    dep_cost = self.total_dependency_cost()
    true_inputs = apparent_inputs + dep_cost["total_true_cost"]

    avg_sustainability = sum(
        d.sustainability_index() for d in self.dependencies.values()
    ) / len(self.dependencies) if self.dependencies else 1

    return (yield_value * avg_sustainability) / true_inputs

def system_health_index(self) -> float:
    """
    Overall system health index (0-1).
    Weighted combination of dependency, ecological, soil, and nutrient health.
    """
    dep_health = sum(
        d.sustainability_index() for d in self.dependencies.values()
    ) / len(self.dependencies) if self.dependencies else 1

    eco_health = self.ecological_metrics.get("ecological_health", 0.5)
    soil_health = max(0, self.production_metrics.get("soil_trend", 0) + 0.5)
    nutrient = self.production_metrics.get("nutrient_density", 0.5)

    health = (
        dep_health * 0.3 +
        eco_health * 0.3 +
        soil_health * 0.2 +
        nutrient * 0.2
    )
    return min(1.0, max(0, health))

def dependency_risk_report(self) -> Dict[str, Any]:
    """Report on dependencies depleting faster than threshold."""
    risks = []
    for name, dep in self.dependencies.items():
        if dep.degradation_rate > 0.1:
            risks.append({
                "dependency": name,
                "risk": "depleting",
                "rate": dep.degradation_rate,
                "years_remaining": 1 / dep.degradation_rate if dep.degradation_rate > 0 else float('inf'),
                "alternative_cost": dep.alternative_cost
            })
    return {
        "total_risks": len(risks),
        "critical_risks": [r for r in risks if r.get("years_remaining", 100) < 20],
        "all_risks": risks
    }
```

# —————————

# System Factory

# —————————

def create_system(
production_metrics: Dict[str, float],
ecological_metrics: Dict[str, float],
dependencies: List[Dependency]
) -> ExpandedFieldSystem:
“””
Generic factory: build a system from metrics and dependency list.

```
Parameters
----------
production_metrics : dict
    Keys: output_yield, input_energy, soil_trend, nutrient_density,
          waste_factor, water_use, fertilizer_use, pesticide_use
ecological_metrics : dict
    Keys: ecological_health, biodiversity_index, water_cycle_health,
          air_quality_impact
dependencies : list[Dependency]
    All externalized or internalized dependencies.

Returns
-------
ExpandedFieldSystem
"""
system = ExpandedFieldSystem()
system.set_production_metrics(production_metrics)
system.set_ecological_metrics(ecological_metrics)
for dep in dependencies:
    system.register_dependency(dep)
return system
```

# —————————

# Comparison

# —————————

def compare_systems(systems: Dict[str, ExpandedFieldSystem]) -> Dict[str, Dict[str, Any]]:
“””
Compare N systems on true efficiency, health, externalization, risk.

```
Parameters
----------
systems : dict[str, ExpandedFieldSystem]
    Named systems to compare.

Returns
-------
dict  keyed by system name → metric dict
"""
results = {}
for name, system in systems.items():
    dep_cost = system.total_dependency_cost()
    risk = system.dependency_risk_report()
    results[name] = {
        "true_efficiency": system.true_system_efficiency(),
        "system_health": system.system_health_index(),
        "externalization_ratio": dep_cost["externalization_ratio"],
        "total_hidden_subsidy": dep_cost["total_hidden_subsidy"],
        "total_true_cost": dep_cost["total_true_cost"],
        "critical_risks": len(risk["critical_risks"]),
        "total_risks": risk["total_risks"],
        "dependency_details": dep_cost["details"]
    }
return results
```
