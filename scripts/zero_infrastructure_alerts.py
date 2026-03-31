# zero_infrastructure_alerts.py

# Alert systems from environmental signals — no infrastructure required

# Generic framework: register signals and alert systems, then weave networks

from dataclasses import dataclass, field
from typing import Dict, List, Any, Optional, Callable
import itertools

# —————————

# Environmental Signal

# —————————

@dataclass
class EnvironmentalSignal:
“”“A signal detectable without infrastructure.”””
name: str
source: str
detection_method: str
what_it_indicates: List[str]
range_meters: float
reliability: float           # 0-1
requires_power: bool
tags: Dict[str, str] = field(default_factory=dict)

# —————————

# Alert System

# —————————

@dataclass
class AlertSystem:
“”“An alert system assembled from environmental signals.”””
name: str
signals: List[str]           # signal names used
detection_method: str
what_it_detects: List[str]
range_meters: float
setup_time_minutes: float
materials_needed: List[str]
reliability: float

# —————————

# Coupling Rule

# —————————

@dataclass
class AlertCouplingRule:
“”“Detects synergy between two alert systems.”””
name: str
requires: List[str]          # alert system names
description: str
strength: float = 0.7

# —————————

# Signal Library

# —————————

class SignalLibrary:
“”“Registry of environmental signals. Populate via register().”””

```
def __init__(self):
    self.signals: Dict[str, EnvironmentalSignal] = {}

def register(self, signal: EnvironmentalSignal):
    self.signals[signal.name] = signal

def passive(self) -> List[EnvironmentalSignal]:
    return [s for s in self.signals.values() if not s.requires_power]

def by_range(self, minimum: float) -> List[EnvironmentalSignal]:
    return [s for s in self.signals.values() if s.range_meters >= minimum]
```

# —————————

# Alert System Library

# —————————

class AlertSystemLibrary:
“”“Registry of alert systems. Populate via register().”””

```
def __init__(self):
    self.systems: Dict[str, AlertSystem] = {}

def register(self, system: AlertSystem):
    self.systems[system.name] = system

def by_reliability(self, minimum: float) -> List[AlertSystem]:
    return [s for s in self.systems.values() if s.reliability >= minimum]

def by_materials(self, available: List[str]) -> List[AlertSystem]:
    """Systems whose materials are all in the available list."""
    result = []
    for sys in self.systems.values():
        if all(
            any(m in available for m in [mat, mat.split()[0]])
            for mat in sys.materials_needed
        ) or not sys.materials_needed:
            result.append(sys)
    return result

def all(self) -> List[AlertSystem]:
    return list(self.systems.values())
```

# —————————

# Alert Network Weaver

# —————————

class AlertNetworkWeaver:
“”“Weave alert systems into a geometric network.”””

```
def __init__(
    self,
    alert_library: AlertSystemLibrary,
    coupling_rules: Optional[List[AlertCouplingRule]] = None,
    max_systems: int = 8,
):
    self.library = alert_library
    self.coupling_rules = coupling_rules or []
    self.max_systems = max_systems

def select(
    self,
    available_materials: List[str],
    sort_key: Optional[Callable[[AlertSystem], float]] = None,
) -> List[str]:
    """
    Select feasible alert systems ranked by sort_key.
    Default sort: reliability desc, range desc.
    """
    feasible = self.library.by_materials(available_materials)
    if sort_key is None:
        sort_key = lambda s: (-s.reliability, -s.range_meters)
    feasible.sort(key=sort_key)
    return [s.name for s in feasible[: self.max_systems]]

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

def create_network(
    self, available_materials: List[str], name: str = "Alert Network"
) -> Dict[str, Any]:
    selected = self.select(available_materials)
    couplings = self.identify_couplings(selected)
    metrics = self.geometric_metrics(selected, couplings)

    # Coverage summary
    all_detects: set = set()
    for sn in selected:
        sys = self.library.systems.get(sn)
        if sys:
            all_detects.update(sys.what_it_detects)

    return {
        "name": name,
        "available_materials": available_materials,
        "selected_systems": selected,
        "couplings": couplings,
        "geometric_metrics": metrics,
        "coverage": sorted(all_detects),
    }
```
