#!/usr/bin/env python3
"""
desert_sand_energy_coupling.py

Physics framework for multi-domain energy coupling from substrate materials.

Models how energy can be extracted from environmental substrates (e.g., desert
sand) by coupling multiple physics domains -- mechanical, thermal, electromagnetic,
piezoelectric, triboelectric, etc. Provides a generic registry of coupling
techniques, a synergy detection engine, and a weaving system that combines
couplings into integrated energy harvesting architectures.

Key concepts:
    - EnergyCoupling: a single technique with efficiency, power density,
      scalability, environment suitability, and resonance characteristics.
    - CouplingLibrary: registry populated via register(); queryable by
      physics domain, environment tag, scalability, resonance, or material.
    - SynergyEngine: pluggable rule engine that detects beneficial
      interactions between pairs of couplings.
    - CouplingWeaver: composes couplings into integrated systems, computing
      aggregate power density, efficiency, environment fit, and novel
      multi-physics or multi-resonant characteristics.

References:
    - Priya, S. & Inman, D.J. (2009). Energy Harvesting Technologies.
      Springer.
    - Beeby, S.P., Tudor, M.J. & White, N.M. (2006). "Energy harvesting
      vibration sources for microsystems applications." Measurement Science
      and Technology, 17(12), R175.
    - Fan, F.R., Tian, Z.Q. & Wang, Z.L. (2012). "Flexible triboelectric
      generator." Nano Energy, 1(2), 328-334.
    - Prigogine, I. & Nicolis, G. (1977). Self-Organization in
      Non-Equilibrium Systems. Wiley.

Usage:
    python3 scripts/desert_sand_energy_coupling.py --demo
    python3 scripts/desert_sand_energy_coupling.py --demo --json
    python3 scripts/desert_sand_energy_coupling.py --help
"""

import math
import json
import sys
import argparse
import itertools
from dataclasses import dataclass, field
from typing import Dict, List, Any, Optional, Tuple, Callable
from enum import Enum
from collections import defaultdict

# ------------------
# Physics Domains
# ------------------


class PhysicsDomain(Enum):
    """Physics domains available for coupling."""
    MECHANICAL = "mechanical"
    THERMAL = "thermal"
    ELECTROMAGNETIC = "electromagnetic"
    QUANTUM = "quantum"
    ACOUSTIC = "acoustic"
    OPTICAL = "optical"
    CHEMICAL = "chemical"
    GRAVITATIONAL = "gravitational"
    FLUID_DYNAMIC = "fluid_dynamic"
    THERMOELECTRIC = "thermoelectric"
    PIEZOELECTRIC = "piezoelectric"
    PYROELECTRIC = "pyroelectric"
    TRIBOELECTRIC = "triboelectric"
    MAGNETIC = "magnetic"
    RADIO_FREQUENCY = "radio_frequency"


@dataclass
class EnergyCoupling:
    """A coupling technique to extract energy from a substrate."""
    name: str
    physics: List[PhysicsDomain]
    mechanism: str
    efficiency: float               # 0-1
    power_density: Optional[float]  # W/m² or W/kg (None if enhancement-only)
    scalability: float              # 0-1
    environment_fit: Dict[str, float] = field(default_factory=dict)
    # environment tag -> 0-1 suitability
    resonance_frequency: Optional[float] = None  # Hz, if resonant
    materials_needed: List[str] = field(default_factory=list)
    status: str = ""


# ------------------
# Coupling Library
# ------------------


class CouplingLibrary:
    """Registry of energy coupling techniques. Populate via register()."""

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


# ------------------
# Synergy Rule Engine
# ------------------


@dataclass
class SynergyRule:
    """Pluggable rule for detecting synergy between two couplings."""
    name: str
    match_a: Callable[[EnergyCoupling], bool]
    match_b: Callable[[EnergyCoupling], bool]
    description: str
    bonus: float = 0.1  # additive power-density or EROI bonus factor


class SynergyEngine:
    """Detects synergies via pluggable rules."""

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


# ------------------
# Coupling Weaver
# ------------------


class CouplingWeaver:
    """Weaves coupling techniques into integrated energy systems."""

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
            return {"name": name, "error": f"No couplings for '{tag}' >= {threshold}"}
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


# ------------------
# Demo / CLI
# ------------------


def _build_demo_library() -> CouplingLibrary:
    """Build a demonstration library with sample desert-sand couplings."""
    lib = CouplingLibrary()

    lib.register(EnergyCoupling(
        name="Piezoelectric Sand Compression",
        physics=[PhysicsDomain.PIEZOELECTRIC, PhysicsDomain.MECHANICAL],
        mechanism="Quartz-bearing sand grains under cyclic mechanical stress "
                  "generate charge via direct piezoelectric effect.",
        efficiency=0.15,
        power_density=0.5,
        scalability=0.7,
        environment_fit={"desert": 0.9, "coastal": 0.6},
        resonance_frequency=40.0,
        materials_needed=["quartz sand", "electrode array"],
        status="theoretical",
    ))

    lib.register(EnergyCoupling(
        name="Triboelectric Wind-Sand",
        physics=[PhysicsDomain.TRIBOELECTRIC, PhysicsDomain.MECHANICAL],
        mechanism="Wind-driven sand particle collisions generate charge "
                  "separation via triboelectric effect.",
        efficiency=0.08,
        power_density=0.2,
        scalability=0.8,
        environment_fit={"desert": 0.95, "coastal": 0.5},
        materials_needed=["collection electrodes"],
        status="experimental",
    ))

    lib.register(EnergyCoupling(
        name="Thermal Gradient Harvesting",
        physics=[PhysicsDomain.THERMOELECTRIC, PhysicsDomain.THERMAL],
        mechanism="Exploit day-night temperature differential in sand "
                  "layers via Seebeck effect thermoelectric generators.",
        efficiency=0.10,
        power_density=1.5,
        scalability=0.6,
        environment_fit={"desert": 0.95, "arid": 0.8},
        materials_needed=["thermoelectric modules", "heat sinks"],
        status="proven",
    ))

    lib.register(EnergyCoupling(
        name="Pyroelectric Thermal Cycling",
        physics=[PhysicsDomain.PYROELECTRIC, PhysicsDomain.THERMAL],
        mechanism="Rapid temperature fluctuations in surface sand induce "
                  "pyroelectric charge generation in crystalline grains.",
        efficiency=0.05,
        power_density=0.1,
        scalability=0.5,
        environment_fit={"desert": 0.7},
        resonance_frequency=0.001,
        materials_needed=["pyroelectric crystals"],
        status="theoretical",
    ))

    lib.register(EnergyCoupling(
        name="Acoustic Resonance Harvesting",
        physics=[PhysicsDomain.ACOUSTIC, PhysicsDomain.MECHANICAL],
        mechanism="Desert 'singing sand' dune resonance captured via "
                  "tuned acoustic-to-electric transducers.",
        efficiency=0.03,
        power_density=0.05,
        scalability=0.4,
        environment_fit={"desert": 0.6},
        resonance_frequency=90.0,
        materials_needed=["acoustic transducers"],
        status="conceptual",
    ))

    return lib


def _build_demo_synergy_engine() -> SynergyEngine:
    """Build a synergy engine with sample rules."""
    engine = SynergyEngine()

    engine.add_rule(SynergyRule(
        name="Thermo-Piezo Cascade",
        match_a=lambda c: PhysicsDomain.THERMAL in c.physics,
        match_b=lambda c: PhysicsDomain.PIEZOELECTRIC in c.physics,
        description="Thermal expansion drives mechanical stress in "
                    "piezoelectric substrates, cascading energy conversion.",
        bonus=0.12,
    ))

    engine.add_rule(SynergyRule(
        name="Tribo-Acoustic Feedback",
        match_a=lambda c: PhysicsDomain.TRIBOELECTRIC in c.physics,
        match_b=lambda c: PhysicsDomain.ACOUSTIC in c.physics,
        description="Triboelectric particle collisions excite acoustic "
                    "modes; acoustic resonance enhances particle agitation.",
        bonus=0.08,
    ))

    return engine


def _format_weaving(w: Dict[str, Any], indent: int = 0) -> str:
    """Format a weaving result for human-readable output."""
    pad = " " * indent
    lines = []
    lines.append(f"{pad}=== {w['name']} ===")

    if "error" in w:
        lines.append(f"{pad}  Error: {w['error']}")
        return "\n".join(lines)

    lines.append(f"{pad}  Couplings: {', '.join(w.get('couplings', []))}")
    lines.append(f"{pad}  Physics domains: {', '.join(w.get('physics_domains', []))}")
    lines.append(f"{pad}  Materials: {', '.join(w.get('materials', []))}")
    lines.append(f"{pad}  Total power density: {w.get('total_power_density', 0):.3f} W/m2")
    lines.append(f"{pad}  Average efficiency: {w.get('average_efficiency', 0):.3f}")
    lines.append(f"{pad}  Average scalability: {w.get('average_scalability', 0):.3f}")

    env = w.get("environment_fit", {})
    if env:
        env_str = ", ".join(f"{k}: {v:.2f}" for k, v in sorted(env.items()))
        lines.append(f"{pad}  Environment fit: {env_str}")

    freq = w.get("frequency_bands", [])
    if freq:
        lines.append(f"{pad}  Frequency bands: {freq}")

    synergies = w.get("synergies", [])
    if synergies:
        lines.append(f"{pad}  Synergies detected: {len(synergies)}")
        for s in synergies:
            lines.append(f"{pad}    - {s['rule']}: {s['description']} (bonus: +{s['bonus']:.2f})")

    novel = w.get("novel_couplings", [])
    if novel:
        lines.append(f"{pad}  Novel couplings:")
        for n in novel:
            lines.append(f"{pad}    - {n}")

    return "\n".join(lines)


def run_demo(use_json: bool = False):
    """Run a demonstration of the coupling framework."""
    lib = _build_demo_library()
    engine = _build_demo_synergy_engine()
    weaver = CouplingWeaver(lib, engine)

    # Weave all desert-suited couplings
    desert_system = weaver.weave_by_environment("desert", "Desert Sand Energy System")

    # Weave by thermal physics domain
    thermal_system = weaver.weave_by_physics(
        PhysicsDomain.THERMAL, "Thermal Harvesting Subsystem"
    )

    # Weave resonant couplings
    resonant_system = weaver.weave_resonant("Resonant Harvesting Subsystem")

    comparison = weaver.compare_weavings()

    if use_json:
        output = {
            "weavings": weaver.weavings,
            "comparison": comparison,
            "library_size": len(lib.all()),
        }
        print(json.dumps(output, indent=2, default=str))
    else:
        print("Desert Sand Energy Coupling Framework -- Demo")
        print("=" * 55)
        print()
        print(f"Registered couplings: {len(lib.all())}")
        print()

        for w in weaver.weavings:
            print(_format_weaving(w))
            print()

        print("-" * 55)
        print("Comparison of weavings:")
        print(f"  {'Name':<35} {'Power':>8} {'Eff':>6} {'Scale':>6} {'Phys':>5} {'Syn':>4}")
        for c in comparison:
            print(
                f"  {c['name']:<35} "
                f"{c['power']:>8.3f} "
                f"{c['efficiency']:>6.3f} "
                f"{c['scalability']:>6.3f} "
                f"{c['physics_count']:>5d} "
                f"{c['synergy_count']:>4d}"
            )


def main():
    parser = argparse.ArgumentParser(
        description=(
            "Physics framework for multi-domain energy coupling from "
            "substrate materials. Models how energy can be extracted from "
            "environmental substrates by coupling multiple physics domains."
        ),
    )
    parser.add_argument(
        "--demo",
        action="store_true",
        help="Run a demonstration with sample desert-sand couplings and synergy rules.",
    )
    parser.add_argument(
        "--json",
        action="store_true",
        help="Output results as JSON instead of human-readable text.",
    )

    args = parser.parse_args()

    if not args.demo:
        parser.print_help()
        sys.exit(0)

    run_demo(use_json=args.json)


if __name__ == "__main__":
    main()
