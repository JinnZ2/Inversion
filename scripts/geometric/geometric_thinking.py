#!/usr/bin/env python3
"""Geometric Thinking — Systems as geometry of coupled vectors.

Models systems as collections of directional vectors in an abstract space.
System health is assessed through geometric properties: the polygon area
formed by vector endpoints (coupling area), directional alignment, effective
dimensionality, and magnitude balance.

Metrics
-------
- **Resultant vector**: Net magnitude and direction from vector summation.
- **Coupling area**: Shoelace-formula area of the polygon formed by vector
  endpoints, sorted by direction. Larger area indicates a more integrated,
  multi-dimensional system.
- **Alignment** (0-1): Ratio of resultant magnitude to total magnitude.
  High alignment means vectors point the same way (linear/rigid system);
  low alignment means forces are distributed (geometric/adaptive system).
- **Dimensionality**: Count of distinct 45-degree sectors occupied by
  active vectors (max 8). Higher dimensionality = richer system geometry.
- **Balance** (0-1): Uniformity of vector magnitudes. 1 = all equal.

References
----------
- Shoelace formula for polygon area (Meister, 1769).
- Vector addition and dot-product geometry (any linear-algebra text).
- Systems-dynamics interpretation follows the Inversion project's
  physics-first validation framework.
"""

import argparse
import json
import math
from dataclasses import dataclass
from typing import Any, Dict, List


@dataclass
class Vector:
    """A direction and magnitude in system space."""
    name: str
    magnitude: float
    direction: float  # degrees

    def dot(self, other: 'Vector') -> float:
        angle_rad = math.radians(self.direction - other.direction)
        return self.magnitude * other.magnitude * math.cos(angle_rad)

    def component_in(self, other: 'Vector') -> float:
        angle_rad = math.radians(self.direction - other.direction)
        return self.magnitude * math.cos(angle_rad)

    def orthogonal_component(self, other: 'Vector') -> float:
        angle_rad = math.radians(self.direction - other.direction)
        return self.magnitude * math.sin(angle_rad)


@dataclass
class SystemGeometry:
    """A system as geometry of coupled vectors."""
    name: str
    vectors: List[Vector]

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
        Larger area -> more integrated system.
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
        """Effective dimensions (distinct 45-degree sectors occupied)."""
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


def compare_geometries(
    systems: List[SystemGeometry],
) -> List[Dict[str, Any]]:
    """Compare N system geometries side by side."""
    return [s.summary() for s in systems]


# ---------------------------------------------------------------------------
# Built-in demo systems
# ---------------------------------------------------------------------------

def _build_demo_systems() -> List[SystemGeometry]:
    """Create three illustrative systems for demonstration."""
    healthy = SystemGeometry("healthy_ecosystem", [
        Vector("producer", 1.0, 0),
        Vector("consumer", 0.9, 72),
        Vector("decomposer", 0.8, 144),
        Vector("regulator", 0.85, 216),
        Vector("connector", 0.95, 288),
    ])

    rigid = SystemGeometry("rigid_institution", [
        Vector("mandate", 1.0, 10),
        Vector("compliance", 0.9, 15),
        Vector("enforcement", 1.0, 5),
        Vector("reporting", 0.7, 12),
        Vector("oversight", 0.3, 8),
    ])

    collapsed = SystemGeometry("collapsed_system", [
        Vector("remnant_a", 0.2, 30),
        Vector("remnant_b", 0.1, 170),
        Vector("noise", 0.05, 300),
    ])

    return [healthy, rigid, collapsed]


# ---------------------------------------------------------------------------
# Human-readable output
# ---------------------------------------------------------------------------

def _print_summary(summary: Dict[str, Any]) -> None:
    """Print a single system summary in human-readable form."""
    print(f"\n  System: {summary['name']}")
    print(f"    Vectors (total / active): {summary['vector_count']} / {summary['active_vectors']}")
    print(f"    Resultant magnitude:      {summary['resultant_magnitude']:.4f}")
    print(f"    Resultant direction:       {summary['resultant_direction']:.2f} deg")
    print(f"    Coupling area:            {summary['coupling_area']:.4f}")
    print(f"    Alignment:                {summary['alignment']:.4f}")
    print(f"    Dimensionality:           {summary['dimensionality']}")
    print(f"    Balance:                  {summary['balance']:.4f}")


def _print_comparison(results: List[Dict[str, Any]]) -> None:
    """Print a side-by-side comparison of systems."""
    print("=" * 60)
    print("  Geometric Thinking — System Comparison")
    print("=" * 60)
    for r in results:
        _print_summary(r)
    print()


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------

def _build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="geometric_thinking",
        description=(
            "Model systems as geometry of coupled vectors. "
            "Computes coupling area, alignment, dimensionality, and balance "
            "for built-in demo systems (healthy ecosystem, rigid institution, "
            "collapsed system)."
        ),
    )
    parser.add_argument(
        "--json",
        action="store_true",
        default=False,
        help="Output results as JSON instead of human-readable text.",
    )
    parser.add_argument(
        "--compare",
        action="store_true",
        default=False,
        help="Compare all demo systems side by side (default behavior).",
    )
    return parser


def main() -> None:
    parser = _build_parser()
    args = parser.parse_args()

    systems = _build_demo_systems()
    results = compare_geometries(systems)

    if args.json:
        print(json.dumps(results, indent=2))
    else:
        _print_comparison(results)


if __name__ == "__main__":
    main()
