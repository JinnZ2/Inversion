#!/usr/bin/env python3
"""
salvage_reclamation.py -- Material reclamation and salvage potential accounting.

Purpose
-------
Models the failure-to-reinventory loop for system components.  Failed
components are decomposed into a material inventory (recoverable metals,
reusable subassemblies, capturable waste heat) that feeds the next design
iteration.  Integrates with system_weaver.py's SystemComponent model.

Core loop:
    Failed components -> material inventory -> next-iteration inputs

Key metrics:
    - effective_salvage: salvage potential gated by available tooling (0-1)
    - innovation_potential: recoverable value / reprocessing cost ratio
    - sovereignty_score: workshop self-sufficiency (tool coverage, material
      diversity, total mass)

References
----------
- Graedel, T. E. & Allenby, B. R. (2003). Industrial Ecology, 2nd ed.
  Prentice Hall.  (material flow analysis, design-for-recycling)
- Stahel, W. R. (2016). "The Circular Economy." Nature 531, 435-438.
  (closed-loop material reclamation)
- Prigogine, I. & Stengers, I. (1984). Order Out of Chaos. Bantam.
  (entropy production in open systems -- entropy_leak_w metric)

Usage
-----
    python3 scripts/salvage_reclamation.py --demo
    python3 scripts/salvage_reclamation.py --demo --json
    python3 scripts/salvage_reclamation.py --help
"""

import argparse
import json
import sys
from dataclasses import dataclass, field
from typing import Dict, List, Any, Optional, Set


# ------------------
# Salvage Profile
# ------------------

@dataclass
class SalvageProfile:
    """
    Salvage characteristics of a system component.
    Attach to any component to track what it yields on failure.
    """
    salvage_potential: float              # 0-1, 1.0 = fully rebuildable from scrap
    recoverable_materials: Dict[str, float]  # material_name -> mass_kg
    reusable_subassemblies: List[str]     # parts usable without reprocessing
    tooling_required: List[str]           # tools needed to reclaim (e.g. "lathe", "smelter")
    entropy_leak_w: float = 0.0          # waste heat (W) that could be captured
    modular_fraction: float = 1.0        # fraction operable if subassembly fails (0-1)

    def effective_salvage(self, available_tools: Set[str]) -> float:
        """
        Salvage potential gated by available tooling.
        Returns 0-1: what fraction of materials can actually be recovered.
        """
        if not self.tooling_required:
            return self.salvage_potential
        tool_coverage = len(available_tools & set(self.tooling_required))
        tool_ratio = tool_coverage / len(self.tooling_required)
        return self.salvage_potential * tool_ratio

    def total_recoverable_mass(self) -> float:
        return sum(self.recoverable_materials.values())


# ------------------
# Reclamation Node
# ------------------

@dataclass
class ReclamationNode:
    """
    A failed component re-indexed as material input.
    Bridges the gap between 'failure' and 'next iteration'.
    """
    component_name: str
    failure_mode: str                     # e.g. "thermal_limit", "wear", "corrosion"
    salvage_profile: SalvageProfile
    retooling_energy_kwh: float           # energy to process salvage
    available_tools: Set[str] = field(default_factory=set)

    def innovation_potential(self) -> float:
        """
        Ratio of recoverable value to reprocessing cost.
        Higher = more worth reclaiming vs discarding.
        """
        effective = self.salvage_profile.effective_salvage(self.available_tools)
        mass = self.salvage_profile.total_recoverable_mass()
        if self.retooling_energy_kwh <= 0:
            return float('inf') if mass > 0 else 0
        return (effective * mass) / self.retooling_energy_kwh

    def harvest(self) -> Dict[str, Any]:
        """
        Execute reclamation: return inventory of recovered materials and parts.
        """
        effective = self.salvage_profile.effective_salvage(self.available_tools)
        return {
            "component": self.component_name,
            "failure_mode": self.failure_mode,
            "raw_materials": {
                mat: mass * effective
                for mat, mass in self.salvage_profile.recoverable_materials.items()
            },
            "reusable_parts": (
                self.salvage_profile.reusable_subassemblies
                if effective > 0.5 else []
            ),
            "capturable_heat_w": self.salvage_profile.entropy_leak_w,
            "effective_salvage": effective,
            "innovation_potential": self.innovation_potential(),
        }


# ------------------
# Workshop Inventory
# ------------------

@dataclass
class WorkshopInventory:
    """
    Tracks available tools, recovered materials, and parts.
    Feeds back into system design: what can be built from what's on hand.
    """
    tools: Set[str] = field(default_factory=set)
    materials: Dict[str, float] = field(default_factory=dict)  # name -> kg
    parts: List[str] = field(default_factory=list)

    def add_tools(self, tools: List[str]):
        self.tools.update(tools)

    def ingest_harvest(self, harvest: Dict[str, Any]):
        """Add reclaimed materials and parts to inventory."""
        for mat, mass in harvest.get("raw_materials", {}).items():
            self.materials[mat] = self.materials.get(mat, 0) + mass
        self.parts.extend(harvest.get("reusable_parts", []))

    def can_build(self, required_materials: Dict[str, float]) -> bool:
        """Check if inventory has enough materials for a build."""
        return all(
            self.materials.get(mat, 0) >= amount
            for mat, amount in required_materials.items()
        )

    def consume(self, required_materials: Dict[str, float]) -> bool:
        """Consume materials for a build. Returns False if insufficient."""
        if not self.can_build(required_materials):
            return False
        for mat, amount in required_materials.items():
            self.materials[mat] -= amount
        return True

    def summary(self) -> Dict[str, Any]:
        return {
            "tools": sorted(self.tools),
            "materials": dict(self.materials),
            "parts": list(self.parts),
            "material_types": len(self.materials),
            "total_mass_kg": sum(self.materials.values()),
        }


# ------------------
# Material Reclamation System
# ------------------

class MaterialReclamationSystem:
    """
    Manages the failure -> harvest -> reinventory loop.
    Components fail; materials are recovered; new builds draw from inventory.
    """

    def __init__(self, inventory: Optional[WorkshopInventory] = None):
        self.inventory = inventory or WorkshopInventory()
        self.reclamation_log: List[Dict[str, Any]] = []

    def register_failure(
        self,
        component_name: str,
        failure_mode: str,
        salvage_profile: SalvageProfile,
        retooling_energy_kwh: float,
    ) -> Dict[str, Any]:
        """
        Process a component failure: harvest and add to inventory.

        Returns harvest report.
        """
        node = ReclamationNode(
            component_name=component_name,
            failure_mode=failure_mode,
            salvage_profile=salvage_profile,
            retooling_energy_kwh=retooling_energy_kwh,
            available_tools=self.inventory.tools,
        )
        harvest = node.harvest()
        self.inventory.ingest_harvest(harvest)
        self.reclamation_log.append(harvest)
        return harvest

    def sovereignty_score(self) -> float:
        """
        How self-sufficient is the workshop?
        Based on tool coverage and material diversity.
        """
        tool_score = min(1.0, len(self.inventory.tools) / 10)
        material_score = min(1.0, len(self.inventory.materials) / 15)
        mass_score = min(1.0, sum(self.inventory.materials.values()) / 500)
        return (tool_score + material_score + mass_score) / 3

    def can_rebuild(
        self, salvage_profile: SalvageProfile
    ) -> Dict[str, Any]:
        """
        Check if a component could be rebuilt from current inventory.
        """
        effective = salvage_profile.effective_salvage(self.inventory.tools)
        buildable = self.inventory.can_build(salvage_profile.recoverable_materials)
        return {
            "effective_salvage": effective,
            "materials_available": buildable,
            "missing_materials": {
                mat: max(0, amount - self.inventory.materials.get(mat, 0))
                for mat, amount in salvage_profile.recoverable_materials.items()
                if self.inventory.materials.get(mat, 0) < amount
            },
            "missing_tools": sorted(
                set(salvage_profile.tooling_required) - self.inventory.tools
            ),
        }

    def summary(self) -> Dict[str, Any]:
        return {
            "reclamations": len(self.reclamation_log),
            "sovereignty_score": self.sovereignty_score(),
            "inventory": self.inventory.summary(),
        }


# ------------------
# Demo / CLI
# ------------------

def run_demo() -> Dict[str, Any]:
    """
    Run a demonstration scenario: a workshop processes two component
    failures and checks whether a third component can be rebuilt.
    """
    # Set up a workshop with basic tools
    workshop = WorkshopInventory()
    workshop.add_tools(["lathe", "smelter", "welder", "drill_press"])

    system = MaterialReclamationSystem(inventory=workshop)

    # First failure: a heat exchanger with corrosion damage
    heat_exchanger_profile = SalvageProfile(
        salvage_potential=0.75,
        recoverable_materials={"copper": 12.5, "steel": 30.0, "aluminum": 5.0},
        reusable_subassemblies=["pressure_gauge", "flow_valve"],
        tooling_required=["smelter", "lathe"],
        entropy_leak_w=450.0,
        modular_fraction=0.6,
    )
    harvest1 = system.register_failure(
        component_name="heat_exchanger_A",
        failure_mode="corrosion",
        salvage_profile=heat_exchanger_profile,
        retooling_energy_kwh=8.0,
    )

    # Second failure: a drive motor with thermal damage
    motor_profile = SalvageProfile(
        salvage_potential=0.55,
        recoverable_materials={"copper": 6.0, "steel": 18.0, "rare_earth": 0.3},
        reusable_subassemblies=["bearing_assembly", "encoder"],
        tooling_required=["lathe", "welder", "magnetizer"],
        entropy_leak_w=200.0,
        modular_fraction=0.4,
    )
    harvest2 = system.register_failure(
        component_name="drive_motor_B",
        failure_mode="thermal_limit",
        salvage_profile=motor_profile,
        retooling_energy_kwh=12.0,
    )

    # Check if we could rebuild the heat exchanger from inventory
    rebuild_check = system.can_rebuild(heat_exchanger_profile)

    return {
        "harvest_1": harvest1,
        "harvest_2": harvest2,
        "rebuild_check_heat_exchanger": rebuild_check,
        "system_summary": system.summary(),
    }


def print_human_readable(results: Dict[str, Any]) -> None:
    """Pretty-print demo results for human consumption."""
    print("=" * 60)
    print("  MATERIAL RECLAMATION SYSTEM -- DEMO")
    print("=" * 60)

    for i, key in enumerate(["harvest_1", "harvest_2"], 1):
        h = results[key]
        print(f"\n--- Harvest {i}: {h['component']} ({h['failure_mode']}) ---")
        print(f"  Effective salvage:      {h['effective_salvage']:.2f}")
        print(f"  Innovation potential:    {h['innovation_potential']:.3f}")
        print(f"  Capturable heat:        {h['capturable_heat_w']:.1f} W")
        print(f"  Recovered materials:")
        for mat, mass in h["raw_materials"].items():
            print(f"    {mat:20s}  {mass:8.2f} kg")
        print(f"  Reusable parts:         {', '.join(h['reusable_parts']) or '(none)'}")

    rc = results["rebuild_check_heat_exchanger"]
    print("\n--- Rebuild Check: heat_exchanger ---")
    print(f"  Materials available:    {rc['materials_available']}")
    print(f"  Effective salvage:      {rc['effective_salvage']:.2f}")
    if rc["missing_materials"]:
        print(f"  Missing materials:")
        for mat, amount in rc["missing_materials"].items():
            print(f"    {mat:20s}  {amount:8.2f} kg needed")
    if rc["missing_tools"]:
        print(f"  Missing tools:          {', '.join(rc['missing_tools'])}")

    s = results["system_summary"]
    print("\n--- System Summary ---")
    print(f"  Total reclamations:     {s['reclamations']}")
    print(f"  Sovereignty score:      {s['sovereignty_score']:.3f}")
    inv = s["inventory"]
    print(f"  Material types:         {inv['material_types']}")
    print(f"  Total mass on hand:     {inv['total_mass_kg']:.2f} kg")
    print(f"  Tools:                  {', '.join(inv['tools'])}")
    print(f"  Parts:                  {', '.join(inv['parts']) or '(none)'}")
    print()


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description=(
            "Material reclamation and salvage potential accounting. "
            "Models the failure-to-reinventory loop: failed components are "
            "decomposed into recoverable materials and reusable subassemblies "
            "that feed the next design iteration."
        ),
    )
    parser.add_argument(
        "--demo",
        action="store_true",
        help="Run a demonstration scenario with sample component failures.",
    )
    parser.add_argument(
        "--json",
        action="store_true",
        help="Output results as JSON instead of human-readable text.",
    )
    return parser


def main() -> None:
    parser = build_parser()
    args = parser.parse_args()

    if not args.demo:
        parser.print_help()
        sys.exit(0)

    results = run_demo()

    if args.json:
        print(json.dumps(results, indent=2))
    else:
        print_human_readable(results)


if __name__ == "__main__":
    main()
