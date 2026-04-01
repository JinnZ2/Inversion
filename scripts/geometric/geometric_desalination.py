#!/usr/bin/env python3
"""
Geometric Desalination — desalination as a geometric system of coupled vectors.

Models desalination infrastructure as a multi-dimensional vector space where each
vector represents a functional dimension (energy input, water output, brine
management, ecological restoration, etc.). System quality is measured by geometric
properties: the "area" (integration proxy) and "integrity" (balance × coupling)
of the resulting polytope.

A pluggable CouplingEngine detects synergies between practices, and the
GeometricDesalinationWeaver composes practices into integrated systems scored
by vector count, coupling density, and geometric potential.

The framework is generic: populate the WisdomLibrary and CouplingEngine via
constructors / register() for any real-world or hypothetical practice set.

References
----------
- Elimelech, M. & Phillip, W. A. (2011). The future of seawater desalination:
  energy, technology, and the environment. *Science*, 333(6043), 712-717.
- Prigogine, I. (1980). *From Being to Becoming*. W. H. Freeman.
- Jones, E. et al. (2019). The state of desalination and brine production:
  a global outlook. *Science of the Total Environment*, 657, 1343-1356.

Usage
-----
    python3 scripts/geometric_desalination.py --demo
    python3 scripts/geometric_desalination.py --demo --json
    python3 scripts/geometric_desalination.py --help
"""

import math
import itertools
import json
import argparse
import sys
from dataclasses import dataclass, field
from typing import Dict, List, Any, Optional, Tuple, Callable
from enum import Enum

# ------------------
# Desalination Vectors
# ------------------


class DesalinationVector(Enum):
    """Possible vectors in a geometric desalination system."""
    ENERGY_INPUT = "energy_input"
    WATER_OUTPUT = "water_output"
    BRINE_MANAGEMENT = "brine_management"
    MINERAL_EXTRACTION = "mineral_extraction"
    MARINE_ECOLOGY = "marine_ecology"
    WASTE_HEAT = "waste_heat"
    RENEWABLE_COUPLING = "renewable_coupling"
    ATMOSPHERIC_HARVEST = "atmospheric_harvest"
    ECOLOGICAL_RESTORATION = "ecological_restoration"
    COMMUNITY_OWNERSHIP = "community_ownership"
    PASSIVE_THERMAL = "passive_thermal"
    WAVE_ENERGY = "wave_energy"
    SOLAR_STILL = "solar_still"
    BIOSALINE_AGRICULTURE = "biosaline_agriculture"


# ------------------
# Desalination System
# ------------------


@dataclass
class DesalinationSystem:
    """Desalination as a geometric system of coupled vectors."""
    name: str
    vectors: Dict[DesalinationVector, float]
    couplings: Dict[Tuple[DesalinationVector, DesalinationVector], float]

    def active_vectors(self) -> List[DesalinationVector]:
        return [v for v, mag in self.vectors.items() if mag > 0]

    def area(self) -> float:
        """
        Geometric proxy for system integration.
        Larger -> more coupled, more resilient.
        """
        active = self.active_vectors()
        if len(active) < 3:
            return 0
        avg_mag = sum(
            self.vectors[v] for v in active
        ) / len(active)
        coupling_factor = (
            sum(self.couplings.values()) / len(self.couplings)
            if self.couplings else 0
        )
        return avg_mag * coupling_factor * len(active) / 8

    def integrity(self) -> float:
        """
        Geometric integrity (0-1).
        Balance of magnitudes x average coupling strength.
        """
        active = [self.vectors[v] for v in self.active_vectors()]
        if not active:
            return 0
        avg = sum(active) / len(active)
        balance = (
            1 - (sum(abs(m - avg) for m in active) / (len(active) * avg))
            if avg > 0 else 0
        )
        coupling_avg = (
            sum(self.couplings.values()) / len(self.couplings)
            if self.couplings else 0
        )
        return balance * 0.5 + coupling_avg * 0.5

    def summary(self) -> Dict[str, Any]:
        return {
            "name": self.name,
            "active_vectors": len(self.active_vectors()),
            "total_vectors": len(self.vectors),
            "area": self.area(),
            "integrity": self.integrity(),
        }


# ------------------
# Desalination Wisdom
# ------------------


@dataclass
class DesalinationWisdom:
    """A desalination practice with its vector coverage and coupling potential."""
    name: str
    mechanism: str
    vectors: List[DesalinationVector]
    efficiency: float
    coupling_potential: List[str]
    tags: Dict[str, str] = field(default_factory=dict)
    # arbitrary metadata: origin, status, etc.


class DesalinationWisdomLibrary:
    """Registry of desalination practices. Populate via register()."""

    def __init__(self):
        self.practices: Dict[str, DesalinationWisdom] = {}

    def register(self, practice: DesalinationWisdom):
        self.practices[practice.name] = practice

    def by_vector(self, vector: DesalinationVector) -> List[DesalinationWisdom]:
        return [
            p for p in self.practices.values() if vector in p.vectors
        ]

    def all(self) -> List[DesalinationWisdom]:
        return list(self.practices.values())


# ------------------
# Coupling Rule Engine
# ------------------


@dataclass
class CouplingRule:
    """Pluggable rule detecting coupling between two practices."""
    name: str
    match_a: Callable[[DesalinationWisdom], bool]
    match_b: Callable[[DesalinationWisdom], bool]
    description: str


class CouplingEngine:
    def __init__(self):
        self.rules: List[CouplingRule] = []

    def add_rule(self, rule: CouplingRule):
        self.rules.append(rule)

    def detect(
        self, practices: List[DesalinationWisdom]
    ) -> List[Dict[str, Any]]:
        found = []
        for p1, p2 in itertools.combinations(practices, 2):
            for rule in self.rules:
                if (rule.match_a(p1) and rule.match_b(p2)) or \
                   (rule.match_a(p2) and rule.match_b(p1)):
                    found.append({
                        "rule": rule.name,
                        "practices": [p1.name, p2.name],
                        "description": rule.description,
                    })
        return found


# ------------------
# Geometric Desalination Weaver
# ------------------


class GeometricDesalinationWeaver:
    """Weaves desalination practices into geometric systems."""

    def __init__(
        self,
        library: DesalinationWisdomLibrary,
        coupling_engine: Optional[CouplingEngine] = None,
    ):
        self.library = library
        self.coupling_engine = coupling_engine or CouplingEngine()
        self.weavings: List[Dict[str, Any]] = []

    def weave(
        self, practice_names: List[str], name: str
    ) -> Dict[str, Any]:
        """Weave named practices into an integrated system."""
        practices = [
            self.library.practices[p]
            for p in practice_names
            if p in self.library.practices
        ]

        all_vectors: set = set()
        for p in practices:
            all_vectors.update(p.vectors)

        couplings = self.coupling_engine.detect(practices)

        vector_count = len(all_vectors)
        coupling_count = len(couplings)
        possible = vector_count * (vector_count - 1) / 2 if vector_count > 1 else 1
        coupling_density = coupling_count / possible

        weaving = {
            "name": name,
            "practices": practice_names,
            "vectors": sorted(v.value for v in all_vectors),
            "couplings": couplings,
            "vector_count": vector_count,
            "coupling_count": coupling_count,
            "coupling_density": coupling_density,
            "geometric_potential": vector_count * coupling_density,
        }

        self.weavings.append(weaving)
        return weaving

    def weave_all(self, name: str = "Complete System") -> Dict[str, Any]:
        return self.weave(list(self.library.practices.keys()), name)

    def compare_weavings(self) -> List[Dict[str, Any]]:
        return [
            {
                "name": w["name"],
                "vectors": w["vector_count"],
                "couplings": w["coupling_count"],
                "density": w["coupling_density"],
                "potential": w["geometric_potential"],
            }
            for w in self.weavings
        ]


# ------------------
# Demo / CLI
# ------------------


def build_demo_library() -> DesalinationWisdomLibrary:
    """Build a small demonstration library of desalination practices."""
    lib = DesalinationWisdomLibrary()

    lib.register(DesalinationWisdom(
        name="Solar Still Array",
        mechanism="Passive solar evaporation with condensation recovery",
        vectors=[
            DesalinationVector.SOLAR_STILL,
            DesalinationVector.PASSIVE_THERMAL,
            DesalinationVector.WATER_OUTPUT,
        ],
        efficiency=0.35,
        coupling_potential=["waste_heat_recovery", "biosaline_irrigation"],
        tags={"origin": "traditional", "status": "proven"},
    ))

    lib.register(DesalinationWisdom(
        name="Wave-Powered RO",
        mechanism="Direct wave-energy pressurisation for reverse osmosis",
        vectors=[
            DesalinationVector.WAVE_ENERGY,
            DesalinationVector.RENEWABLE_COUPLING,
            DesalinationVector.WATER_OUTPUT,
            DesalinationVector.ENERGY_INPUT,
        ],
        efficiency=0.55,
        coupling_potential=["marine_ecology_monitoring", "brine_dispersal"],
        tags={"origin": "engineering", "status": "prototype"},
    ))

    lib.register(DesalinationWisdom(
        name="Brine-to-Mineral Recovery",
        mechanism="Selective crystallisation extracting Li, Mg, Na salts from RO brine",
        vectors=[
            DesalinationVector.BRINE_MANAGEMENT,
            DesalinationVector.MINERAL_EXTRACTION,
        ],
        efficiency=0.40,
        coupling_potential=["waste_heat_input", "biosaline_agriculture"],
        tags={"origin": "chemistry", "status": "pilot"},
    ))

    lib.register(DesalinationWisdom(
        name="Biosaline Agroforestry",
        mechanism="Salt-tolerant crops irrigated with diluted brine",
        vectors=[
            DesalinationVector.BIOSALINE_AGRICULTURE,
            DesalinationVector.ECOLOGICAL_RESTORATION,
            DesalinationVector.BRINE_MANAGEMENT,
        ],
        efficiency=0.30,
        coupling_potential=["community_ownership", "marine_ecology"],
        tags={"origin": "agroecology", "status": "established"},
    ))

    lib.register(DesalinationWisdom(
        name="Community Fog Harvesting",
        mechanism="Mesh-net atmospheric water capture with community governance",
        vectors=[
            DesalinationVector.ATMOSPHERIC_HARVEST,
            DesalinationVector.COMMUNITY_OWNERSHIP,
            DesalinationVector.WATER_OUTPUT,
        ],
        efficiency=0.20,
        coupling_potential=["ecological_restoration", "solar_still"],
        tags={"origin": "indigenous", "status": "proven"},
    ))

    return lib


def build_demo_coupling_engine() -> CouplingEngine:
    """Build a coupling engine with example rules for the demo library."""
    engine = CouplingEngine()

    engine.add_rule(CouplingRule(
        name="brine_loop",
        match_a=lambda p: DesalinationVector.BRINE_MANAGEMENT in p.vectors,
        match_b=lambda p: DesalinationVector.MINERAL_EXTRACTION in p.vectors
            or DesalinationVector.BIOSALINE_AGRICULTURE in p.vectors,
        description="Brine output of one practice feeds mineral or agricultural input of another",
    ))

    engine.add_rule(CouplingRule(
        name="renewable_energy_share",
        match_a=lambda p: DesalinationVector.RENEWABLE_COUPLING in p.vectors
            or DesalinationVector.WAVE_ENERGY in p.vectors,
        match_b=lambda p: DesalinationVector.ENERGY_INPUT in p.vectors
            or DesalinationVector.PASSIVE_THERMAL in p.vectors,
        description="Renewable energy generated by one practice powers another",
    ))

    engine.add_rule(CouplingRule(
        name="community_governance",
        match_a=lambda p: DesalinationVector.COMMUNITY_OWNERSHIP in p.vectors,
        match_b=lambda p: DesalinationVector.ECOLOGICAL_RESTORATION in p.vectors,
        description="Community governance couples with ecological restoration feedback",
    ))

    return engine


def run_demo(as_json: bool = False):
    """Run the demonstration: build library, weave systems, print results."""
    lib = build_demo_library()
    engine = build_demo_coupling_engine()
    weaver = GeometricDesalinationWeaver(lib, engine)

    # Weave a partial system
    partial = weaver.weave(
        ["Solar Still Array", "Brine-to-Mineral Recovery"],
        name="Partial: Solar + Mineral",
    )

    # Weave a broader system
    broad = weaver.weave(
        ["Wave-Powered RO", "Brine-to-Mineral Recovery",
         "Biosaline Agroforestry"],
        name="Broad: Wave + Mineral + Agro",
    )

    # Weave the complete system
    complete = weaver.weave_all(name="Complete Demo System")

    comparison = weaver.compare_weavings()

    if as_json:
        output = {
            "weavings": weaver.weavings,
            "comparison": comparison,
        }
        print(json.dumps(output, indent=2))
        return

    # Human-readable output
    print("=" * 60)
    print("GEOMETRIC DESALINATION — Demo Weavings")
    print("=" * 60)

    for w in weaver.weavings:
        print()
        print(f"--- {w['name']} ---")
        print(f"  Practices:          {', '.join(w['practices'])}")
        print(f"  Vectors ({w['vector_count']:>2}):       {', '.join(w['vectors'])}")
        print(f"  Couplings found:    {w['coupling_count']}")
        print(f"  Coupling density:   {w['coupling_density']:.3f}")
        print(f"  Geometric potential: {w['geometric_potential']:.3f}")
        if w["couplings"]:
            print("  Coupling details:")
            for c in w["couplings"]:
                print(f"    [{c['rule']}] {c['practices'][0]} <-> {c['practices'][1]}")
                print(f"      {c['description']}")

    print()
    print("=" * 60)
    print("COMPARISON")
    print("=" * 60)
    print(f"  {'Name':<35} {'Vec':>4} {'Coup':>5} {'Dens':>7} {'Potntl':>7}")
    print(f"  {'-'*35} {'-'*4} {'-'*5} {'-'*7} {'-'*7}")
    for row in comparison:
        print(
            f"  {row['name']:<35} {row['vectors']:>4} "
            f"{row['couplings']:>5} {row['density']:>7.3f} "
            f"{row['potential']:>7.3f}"
        )
    print()


def main():
    parser = argparse.ArgumentParser(
        description=(
            "Geometric Desalination — model desalination infrastructure as "
            "a geometric system of coupled vectors. Practices are composed "
            "into integrated systems scored by vector count, coupling density, "
            "and geometric potential."
        ),
    )
    parser.add_argument(
        "--demo",
        action="store_true",
        help="Run a built-in demonstration with sample practices and couplings",
    )
    parser.add_argument(
        "--json",
        action="store_true",
        dest="as_json",
        help="Output results as JSON instead of human-readable text",
    )

    args = parser.parse_args()

    if args.demo:
        run_demo(as_json=args.as_json)
    else:
        parser.print_help()
        sys.exit(0)


if __name__ == "__main__":
    main()
