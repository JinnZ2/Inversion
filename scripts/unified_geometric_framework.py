# unified_geometric_framework.py

# Unified geometry of coupled systems

# Applicable to any domain: agriculture, energy, water, economics, etc.

import math
import itertools
from dataclasses import dataclass, field
from typing import Dict, List, Any, Optional, Tuple, Set
from collections import defaultdict

# —————————

# Core Geometric Structures

# —————————

@dataclass
class Vector:
“”“A dimension of system health.”””
name: str
magnitude: float    # 0-1, current state
direction: float    # degrees, angular position in system space
domain: str = “”    # which system domain
target: float = 1.0 # desired magnitude

```
def component_in(self, other: 'Vector') -> float:
    angle_rad = math.radians(self.direction - other.direction)
    return self.magnitude * math.cos(angle_rad)

def orthogonal_component(self, other: 'Vector') -> float:
    angle_rad = math.radians(self.direction - other.direction)
    return self.magnitude * math.sin(angle_rad)
```

@dataclass
class Coupling:
“”“An interaction between two vectors.”””
v1: str
v2: str
strength: float     # 0-1
mechanism: str = “”
synergy: float = 1.0  # multiplicative effect (>1 = positive)

@dataclass
class GeometricSystem:
“”“A system as geometry of coupled vectors.”””
name: str
domain: str
vectors: Dict[str, Vector]
couplings: Dict[Tuple[str, str], Coupling]

```
def active_vectors(self) -> List[Vector]:
    return [v for v in self.vectors.values() if v.magnitude > 0]

def active_couplings(self) -> List[Coupling]:
    return [c for c in self.couplings.values() if c.strength > 0]

def coupling_density(self) -> float:
    """Ratio of actual to possible couplings among active vectors."""
    n = len(self.active_vectors())
    if n < 2:
        return 0
    possible = n * (n - 1) / 2
    return len(self.active_couplings()) / possible

def vector_balance(self) -> float:
    """How balanced magnitudes are (0-1). 1 = all equal."""
    active = [v.magnitude for v in self.active_vectors()]
    if not active:
        return 0
    avg = sum(active) / len(active)
    if avg == 0:
        return 0
    variance = sum(abs(m - avg) for m in active) / len(active)
    return max(0, 1 - variance / avg)

def coupling_strength_avg(self) -> float:
    active = self.active_couplings()
    return sum(c.strength for c in active) / len(active) if active else 0

def coupling_synergy_avg(self) -> float:
    active = self.active_couplings()
    return sum(c.synergy for c in active) / len(active) if active else 1.0

def polygon_area(self) -> float:
    """
    Area of the polygon formed by vector endpoints.
    Larger → more integrated, more resilient.
    Scaled by coupling synergy.
    """
    active = sorted(self.active_vectors(), key=lambda v: v.direction)
    if len(active) < 3:
        return 0

    area = 0.0
    for i in range(len(active)):
        v1 = active[i]
        v2 = active[(i + 1) % len(active)]
        x1 = v1.magnitude * math.cos(math.radians(v1.direction))
        y1 = v1.magnitude * math.sin(math.radians(v1.direction))
        x2 = v2.magnitude * math.cos(math.radians(v2.direction))
        y2 = v2.magnitude * math.sin(math.radians(v2.direction))
        area += x1 * y2 - x2 * y1

    area = abs(area) / 2
    coupling_factor = 1 + (
        self.coupling_density()
        * self.coupling_strength_avg()
        * (self.coupling_synergy_avg() - 1)
    )
    return area * coupling_factor

def integrity(self) -> float:
    """
    Geometric integrity (0-1).
    Combines area ratio, balance, and coupling density.
    """
    active = self.active_vectors()
    if not active:
        return 0

    n = len(active)
    max_area = (n * math.sin(2 * math.pi / n)) / 2 if n >= 3 else 1.0
    actual = self.polygon_area()
    area_ratio = min(1.0, actual / max_area) if max_area > 0 else 0

    return min(1.0, (
        area_ratio * 0.4
        + self.vector_balance() * 0.3
        + self.coupling_density() * 0.2
        + self.coupling_strength_avg() * 0.1
    ))

def emergent_properties(self) -> List[str]:
    """Properties that emerge from the geometry."""
    props = []
    integrity = self.integrity()
    if integrity > 0.7:
        props.append("High resilience: system absorbs shocks")
    elif integrity > 0.4:
        props.append("Moderate resilience")
    else:
        props.append("Fragile: small perturbations may cascade")

    waste = 1 - self.coupling_density()
    if waste > 0.5:
        props.append(f"High uncoupled potential: {waste:.0%} of couplings unused")

    if self.coupling_synergy_avg() > 1.2:
        props.append("Strong synergy across couplings")

    dims = len(self.active_vectors())
    if dims > 6:
        props.append(f"High dimensionality: {dims} active vectors")
    elif dims < 3:
        props.append(f"Low dimensionality: {dims} vectors — linear behavior")

    return props

def summary(self) -> Dict[str, Any]:
    return {
        "name": self.name,
        "domain": self.domain,
        "active_vectors": len(self.active_vectors()),
        "active_couplings": len(self.active_couplings()),
        "coupling_density": self.coupling_density(),
        "vector_balance": self.vector_balance(),
        "polygon_area": self.polygon_area(),
        "integrity": self.integrity(),
        "emergent": self.emergent_properties(),
    }
```

# —————————

# Geometric Analyzer

# —————————

class GeometricAnalyzer:
“”“Analyze and compare geometric systems.”””

```
def __init__(self):
    self.systems: List[GeometricSystem] = []

def add(self, system: GeometricSystem):
    self.systems.append(system)

def compare(self) -> List[Dict[str, Any]]:
    return [s.summary() for s in self.systems]

def rank_by(self, metric: str = "integrity") -> List[Dict[str, Any]]:
    summaries = self.compare()
    return sorted(summaries, key=lambda s: -s.get(metric, 0))
```
