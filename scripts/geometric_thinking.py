# geometric_thinking.py

# Systems as geometry of coupled vectors

# Vector magnitude × direction × coupling → polygon area = system health

import math
from typing import List, Dict, Any, Optional
from dataclasses import dataclass

@dataclass
class Vector:
“”“A direction and magnitude in system space.”””
name: str
magnitude: float
direction: float  # degrees

```
def dot(self, other: 'Vector') -> float:
    angle_rad = math.radians(self.direction - other.direction)
    return self.magnitude * other.magnitude * math.cos(angle_rad)

def component_in(self, other: 'Vector') -> float:
    angle_rad = math.radians(self.direction - other.direction)
    return self.magnitude * math.cos(angle_rad)

def orthogonal_component(self, other: 'Vector') -> float:
    angle_rad = math.radians(self.direction - other.direction)
    return self.magnitude * math.sin(angle_rad)
```

@dataclass
class SystemGeometry:
“”“A system as geometry of coupled vectors.”””
name: str
vectors: List[Vector]

```
def resultant(self) -> Vector:
    """Net vector (sum of all components)."""
    total_x = sum(
        v.magnitude * math.cos(math.radians(v.direction))
        for v in self.vectors
    )
    total_y = sum(
        v.magnitude * math.sin(math.radians(v.direction))
        for v in self.vectors
    )
    magnitude = math.sqrt(total_x ** 2 + total_y ** 2)
    direction = math.degrees(math.atan2(total_y, total_x))
    return Vector("resultant", magnitude, direction)

def coupling_area(self) -> float:
    """
    Area of the polygon formed by vector endpoints.
    Larger area → more integrated system.
    """
    if len(self.vectors) < 3:
        return 0
    sorted_v = sorted(self.vectors, key=lambda v: v.direction)
    area = 0.0
    for i in range(len(sorted_v)):
        v1 = sorted_v[i]
        v2 = sorted_v[(i + 1) % len(sorted_v)]
        x1 = v1.magnitude * math.cos(math.radians(v1.direction))
        y1 = v1.magnitude * math.sin(math.radians(v1.direction))
        x2 = v2.magnitude * math.cos(math.radians(v2.direction))
        y2 = v2.magnitude * math.sin(math.radians(v2.direction))
        area += x1 * y2 - x2 * y1
    return abs(area) / 2

def alignment(self) -> float:
    """
    How aligned the vectors are (0-1).
    1 = all same direction (linear system).
    Lower = more distributed (geometric system).
    """
    if not self.vectors:
        return 0
    resultant = self.resultant()
    total_magnitude = sum(v.magnitude for v in self.vectors)
    if total_magnitude == 0:
        return 0
    return resultant.magnitude / total_magnitude

def dimensionality(self) -> int:
    """Effective dimensions (distinct 45° sectors occupied)."""
    directions = set(
        round(v.direction / 45) * 45 for v in self.vectors
        if v.magnitude > 0
    )
    return min(8, len(directions))

def balance(self) -> float:
    """
    How balanced the magnitudes are (0-1).
    1 = all equal magnitude.
    """
    active = [v.magnitude for v in self.vectors if v.magnitude > 0]
    if not active:
        return 0
    avg = sum(active) / len(active)
    if avg == 0:
        return 0
    variance = sum(abs(m - avg) for m in active) / len(active)
    return max(0, 1 - variance / avg)

def summary(self) -> Dict[str, Any]:
    """All geometric metrics."""
    r = self.resultant()
    return {
        "name": self.name,
        "vector_count": len(self.vectors),
        "active_vectors": len([v for v in self.vectors if v.magnitude > 0]),
        "resultant_magnitude": r.magnitude,
        "resultant_direction": r.direction,
        "coupling_area": self.coupling_area(),
        "alignment": self.alignment(),
        "dimensionality": self.dimensionality(),
        "balance": self.balance(),
    }
```

def compare_geometries(
systems: List[SystemGeometry],
) -> List[Dict[str, Any]]:
“”“Compare N system geometries side by side.”””
return [s.summary() for s in systems]
