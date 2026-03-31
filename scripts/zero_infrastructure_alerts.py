#!/usr/bin/env python3
"""
Zero-Infrastructure Alert Systems
==================================

Build alert networks from environmental signals that require no
infrastructure (electricity, internet, supply chains). Registers
detectable signals, assembles them into alert systems, and weaves
systems into a coupled geometric network.

Framework
---------
1. **EnvironmentalSignal** — a single observable (e.g. bird alarm calls,
   wind-carried scent change) with range, reliability, and power requirement.
2. **AlertSystem** — a composite detector assembled from one or more signals,
   with materials list, setup time, and reliability.
3. **AlertCouplingRule** — a synergy rule that fires when two or more alert
   systems are co-present, increasing network integrity.
4. **AlertNetworkWeaver** — selects feasible systems given available materials,
   identifies active couplings, and computes geometric metrics (coupling
   density, average strength, integrity score).

The geometric metrics are inspired by graph-density measures from
algebraic graph theory (Fiedler, 1973) and network resilience analysis
(Albert & Barabasi, 2002).

References
----------
- Fiedler, M. (1973). Algebraic connectivity of graphs.
  *Czechoslovak Mathematical Journal*, 23(2), 298-305.
- Albert, R., & Barabasi, A.-L. (2002). Statistical mechanics of
  complex networks. *Reviews of Modern Physics*, 74(1), 47-97.
- Prigogine, I., & Stengers, I. (1984). *Order Out of Chaos*.

Usage
-----
    python3 scripts/zero_infrastructure_alerts.py --help
    python3 scripts/zero_infrastructure_alerts.py --demo
    python3 scripts/zero_infrastructure_alerts.py --demo --json
"""

from dataclasses import dataclass, field
from typing import Dict, List, Any, Optional, Callable
import argparse
import itertools
import json
import sys

# ------------------------------------------------------------------
# Environmental Signal
# ------------------------------------------------------------------


@dataclass
class EnvironmentalSignal:
    """A signal detectable without infrastructure."""
    name: str
    source: str
    detection_method: str
    what_it_indicates: List[str]
    range_meters: float
    reliability: float           # 0-1
    requires_power: bool
    tags: Dict[str, str] = field(default_factory=dict)


# ------------------------------------------------------------------
# Alert System
# ------------------------------------------------------------------


@dataclass
class AlertSystem:
    """An alert system assembled from environmental signals."""
    name: str
    signals: List[str]           # signal names used
    detection_method: str
    what_it_detects: List[str]
    range_meters: float
    setup_time_minutes: float
    materials_needed: List[str]
    reliability: float


# ------------------------------------------------------------------
# Coupling Rule
# ------------------------------------------------------------------


@dataclass
class AlertCouplingRule:
    """Detects synergy between two alert systems."""
    name: str
    requires: List[str]          # alert system names
    description: str
    strength: float = 0.7


# ------------------------------------------------------------------
# Signal Library
# ------------------------------------------------------------------


class SignalLibrary:
    """Registry of environmental signals. Populate via register()."""

    def __init__(self):
        self.signals: Dict[str, EnvironmentalSignal] = {}

    def register(self, signal: EnvironmentalSignal):
        self.signals[signal.name] = signal

    def passive(self) -> List[EnvironmentalSignal]:
        return [s for s in self.signals.values() if not s.requires_power]

    def by_range(self, minimum: float) -> List[EnvironmentalSignal]:
        return [s for s in self.signals.values() if s.range_meters >= minimum]


# ------------------------------------------------------------------
# Alert System Library
# ------------------------------------------------------------------


class AlertSystemLibrary:
    """Registry of alert systems. Populate via register()."""

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


# ------------------------------------------------------------------
# Alert Network Weaver
# ------------------------------------------------------------------


class AlertNetworkWeaver:
    """Weave alert systems into a geometric network."""

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


# ------------------------------------------------------------------
# Demo data
# ------------------------------------------------------------------


def _build_demo() -> Dict[str, Any]:
    """Build a demo signal library, alert systems, coupling rules,
    and return the resulting network dict."""

    # --- signals ---
    sig_lib = SignalLibrary()
    sig_lib.register(EnvironmentalSignal(
        name="bird_alarm",
        source="songbirds",
        detection_method="listen for alarm calls",
        what_it_indicates=["predator approach", "human movement"],
        range_meters=200,
        reliability=0.75,
        requires_power=False,
    ))
    sig_lib.register(EnvironmentalSignal(
        name="wind_shift",
        source="atmosphere",
        detection_method="feel wind direction change",
        what_it_indicates=["weather change", "fire approach"],
        range_meters=500,
        reliability=0.6,
        requires_power=False,
    ))
    sig_lib.register(EnvironmentalSignal(
        name="ground_vibration",
        source="ground",
        detection_method="feel or listen for vibrations",
        what_it_indicates=["vehicle approach", "large animal movement"],
        range_meters=300,
        reliability=0.65,
        requires_power=False,
    ))
    sig_lib.register(EnvironmentalSignal(
        name="water_clarity",
        source="stream / pond",
        detection_method="observe turbidity change",
        what_it_indicates=["upstream disturbance", "runoff event"],
        range_meters=1000,
        reliability=0.55,
        requires_power=False,
    ))

    # --- alert systems ---
    alert_lib = AlertSystemLibrary()
    alert_lib.register(AlertSystem(
        name="perimeter_bird_watch",
        signals=["bird_alarm"],
        detection_method="station observers at bird-rich edges",
        what_it_detects=["human approach", "predator"],
        range_meters=200,
        setup_time_minutes=5,
        materials_needed=[],
        reliability=0.75,
    ))
    alert_lib.register(AlertSystem(
        name="vibration_line",
        signals=["ground_vibration"],
        detection_method="place containers of water on ground, watch ripples",
        what_it_detects=["vehicle approach", "heavy foot traffic"],
        range_meters=300,
        setup_time_minutes=10,
        materials_needed=["container", "water"],
        reliability=0.65,
    ))
    alert_lib.register(AlertSystem(
        name="wind_scent_net",
        signals=["wind_shift"],
        detection_method="hang light cloth strips to visualise airflow",
        what_it_detects=["fire approach", "chemical release"],
        range_meters=500,
        setup_time_minutes=15,
        materials_needed=["cloth", "string"],
        reliability=0.6,
    ))
    alert_lib.register(AlertSystem(
        name="water_turbidity_watch",
        signals=["water_clarity"],
        detection_method="check upstream water clarity at intervals",
        what_it_detects=["upstream disturbance", "contamination"],
        range_meters=1000,
        setup_time_minutes=5,
        materials_needed=["container", "water"],
        reliability=0.55,
    ))

    # --- coupling rules ---
    rules = [
        AlertCouplingRule(
            name="bird+vibration",
            requires=["perimeter_bird_watch", "vibration_line"],
            description="birds confirm vibration source is animate",
            strength=0.8,
        ),
        AlertCouplingRule(
            name="wind+water",
            requires=["wind_scent_net", "water_turbidity_watch"],
            description="wind direction + water change triangulates source",
            strength=0.7,
        ),
    ]

    # --- weave ---
    weaver = AlertNetworkWeaver(alert_lib, coupling_rules=rules)
    materials = ["container", "water", "cloth", "string"]
    network = weaver.create_network(materials, name="Demo Alert Network")
    return network


# ------------------------------------------------------------------
# Human-readable output
# ------------------------------------------------------------------


def _print_network(network: Dict[str, Any]) -> None:
    """Pretty-print a network dictionary."""
    print(f"=== {network['name']} ===\n")

    print("Available materials:", ", ".join(network["available_materials"]))
    print()

    print("Selected systems:")
    for s in network["selected_systems"]:
        print(f"  - {s}")
    print()

    print("Couplings:")
    if network["couplings"]:
        for c in network["couplings"]:
            comps = " + ".join(c["components"])
            print(f"  - {comps}  (strength {c['strength']:.2f})")
            print(f"    {c['description']}")
    else:
        print("  (none)")
    print()

    gm = network["geometric_metrics"]
    print("Geometric metrics:")
    print(f"  vectors              : {gm['vectors']}")
    print(f"  couplings            : {gm['couplings']}")
    print(f"  coupling density     : {gm['coupling_density']:.4f}")
    print(f"  avg coupling strength: {gm['avg_coupling_strength']:.4f}")
    print(f"  geometric area       : {gm['geometric_area']:.4f}")
    print(f"  integrity            : {gm['integrity']:.4f}")
    print()

    print("Coverage:")
    for item in network["coverage"]:
        print(f"  - {item}")


# ------------------------------------------------------------------
# CLI
# ------------------------------------------------------------------


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description=(
            "Zero-infrastructure alert systems — build alert networks "
            "from environmental signals that require no electricity, "
            "internet, or supply chains."
        ),
    )
    parser.add_argument(
        "--demo",
        action="store_true",
        help="Run a built-in demo with sample signals, systems, and coupling rules.",
    )
    parser.add_argument(
        "--json",
        action="store_true",
        dest="use_json",
        help="Output results as JSON instead of human-readable text.",
    )
    return parser


def main() -> None:
    parser = build_parser()
    args = parser.parse_args()

    if not args.demo:
        parser.print_help()
        print("\n(Use --demo to run a sample alert network.)")
        sys.exit(0)

    network = _build_demo()

    if args.use_json:
        print(json.dumps(network, indent=2))
    else:
        _print_network(network)


if __name__ == "__main__":
    main()
