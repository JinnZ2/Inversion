# salvage_reclamation.py

# Material reclamation and salvage potential accounting

# Failed components → material inventory → next-iteration inputs

# Integrates with system_weaver.py SystemComponent model

from dataclasses import dataclass, field
from typing import Dict, List, Any, Optional, Set

# —————————

# Salvage Profile

# —————————

@dataclass
class SalvageProfile:
“””
Salvage characteristics of a system component.
Attach to any component to track what it yields on failure.
“””
salvage_potential: float              # 0-1, 1.0 = fully rebuildable from scrap
recoverable_materials: Dict[str, float]  # material_name → mass_kg
reusable_subassemblies: List[str]     # parts usable without reprocessing
tooling_required: List[str]           # tools needed to reclaim (e.g. “lathe”, “smelter”)
entropy_leak_w: float = 0.0          # waste heat (W) that could be captured
modular_fraction: float = 1.0        # fraction operable if subassembly fails (0-1)

```
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
```

# —————————

# Reclamation Node

# —————————

@dataclass
class ReclamationNode:
“””
A failed component re-indexed as material input.
Bridges the gap between ‘failure’ and ‘next iteration’.
“””
component_name: str
failure_mode: str                     # e.g. “thermal_limit”, “wear”, “corrosion”
salvage_profile: SalvageProfile
retooling_energy_kwh: float           # energy to process salvage
available_tools: Set[str] = field(default_factory=set)

```
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
```

# —————————

# Workshop Inventory

# —————————

@dataclass
class WorkshopInventory:
“””
Tracks available tools, recovered materials, and parts.
Feeds back into system design: what can be built from what’s on hand.
“””
tools: Set[str] = field(default_factory=set)
materials: Dict[str, float] = field(default_factory=dict)  # name → kg
parts: List[str] = field(default_factory=list)

```
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
```

# —————————

# Material Reclamation System

# —————————

class MaterialReclamationSystem:
“””
Manages the failure → harvest → reinventory loop.
Components fail; materials are recovered; new builds draw from inventory.
“””

```
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
```
