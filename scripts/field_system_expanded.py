#!/usr/bin/env python3
"""
field_system_expanded.py — Full dependency accounting for agricultural systems.

Framework for internalizing externalized costs in production systems.
Models agricultural (or any production) systems as networks of dependencies,
some of which are externalized onto shared resources (clean water, air,
genetic commons, data infrastructure, etc.).  Computes true costs, system
health indices, and dependency-risk reports.

Analytical grounding
--------------------
* Externality internalisation follows Pigou (1920) and Coase (1960).
* Sustainability index treats each dependency as a depletable stock
  with a first-order degradation rate, consistent with standard
  resource-economics models (Clark, 1990).
* System-health index is a weighted composite inspired by the
  FAO Sustainability Assessment of Food and Agriculture (SAFA)
  framework.

References
----------
Pigou, A. C. (1920). The Economics of Welfare.
Coase, R. H. (1960). The Problem of Social Cost. Journal of Law and
    Economics, 3, 1-44.
Clark, C. W. (1990). Mathematical Bioeconomics (2nd ed.). Wiley.
FAO (2014). SAFA Guidelines, Version 3.0.

Usage
-----
    python3 scripts/field_system_expanded.py --help
    python3 scripts/field_system_expanded.py --demo
    python3 scripts/field_system_expanded.py --demo --json
"""

from dataclasses import dataclass, field
from typing import Dict, Any, List, Optional
from enum import Enum
import argparse
import json
import math
import sys

# ------------------
# Dependency Classification
# ------------------


class DependencyType(Enum):
    """Types of dependencies that production systems may externalize."""
    CLEAN_WATER = "clean_water"
    CLEAN_AIR = "clean_air"
    DATA_INFRASTRUCTURE = "data_infrastructure"
    SATELLITE_SYSTEMS = "satellite_systems"
    PROPRIETARY_SOFTWARE = "proprietary_software"
    GENETIC_IP = "genetic_ip"
    SUPPLY_CHAIN = "supply_chain"
    REGULATORY_COMPLIANCE = "regulatory_compliance"


@dataclass
class Dependency:
    """A dependency that a production system may externalize."""
    name: str
    type: DependencyType
    current_cost: float          # Apparent cost (unit/time)
    hidden_subsidy: float        # Externalized cost (unit/time)
    degradation_rate: float      # Rate of depletion (+) or regeneration (-)
    alternative_cost: float      # Cost of internalized alternative
    measurement_method: str

    def true_cost(self) -> float:
        """True cost including externalized subsidies."""
        return self.current_cost + self.hidden_subsidy

    def sustainability_index(self) -> float:
        """0-1, how sustainable current usage is."""
        return max(0, 1 - self.degradation_rate)


# ------------------
# Expanded Field System
# ------------------


class ExpandedFieldSystem:
    """
    Production system with full dependency accounting.
    Treats shared resources as depletable inputs.
    """

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


# ------------------
# System Factory
# ------------------


def create_system(
    production_metrics: Dict[str, float],
    ecological_metrics: Dict[str, float],
    dependencies: List[Dependency]
) -> ExpandedFieldSystem:
    """
    Generic factory: build a system from metrics and dependency list.

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


# ------------------
# Comparison
# ------------------


def compare_systems(systems: Dict[str, ExpandedFieldSystem]) -> Dict[str, Dict[str, Any]]:
    """
    Compare N systems on true efficiency, health, externalization, risk.

    Parameters
    ----------
    systems : dict[str, ExpandedFieldSystem]
        Named systems to compare.

    Returns
    -------
    dict  keyed by system name -> metric dict
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


# ------------------
# Demo / CLI
# ------------------


def _build_demo_systems() -> Dict[str, ExpandedFieldSystem]:
    """Build example industrial vs. regenerative systems for demonstration."""

    # -- Industrial monoculture --
    industrial_deps = [
        Dependency(
            name="groundwater",
            type=DependencyType.CLEAN_WATER,
            current_cost=50,
            hidden_subsidy=200,
            degradation_rate=0.15,
            alternative_cost=400,
            measurement_method="aquifer drawdown rate (m/yr)"
        ),
        Dependency(
            name="air_quality",
            type=DependencyType.CLEAN_AIR,
            current_cost=0,
            hidden_subsidy=120,
            degradation_rate=0.08,
            alternative_cost=180,
            measurement_method="PM2.5 / NOx emissions (kg/ha/yr)"
        ),
        Dependency(
            name="gps_guidance",
            type=DependencyType.SATELLITE_SYSTEMS,
            current_cost=30,
            hidden_subsidy=60,
            degradation_rate=0.02,
            alternative_cost=90,
            measurement_method="subscription + public infrastructure cost"
        ),
        Dependency(
            name="seed_genetics",
            type=DependencyType.GENETIC_IP,
            current_cost=100,
            hidden_subsidy=150,
            degradation_rate=0.12,
            alternative_cost=80,
            measurement_method="royalty + germplasm narrowing index"
        ),
    ]
    industrial = create_system(
        production_metrics={
            "output_yield": 1000,
            "input_energy": 400,
            "soil_trend": -0.2,
            "nutrient_density": 0.35,
            "water_use": 800,
            "fertilizer_use": 250,
            "pesticide_use": 60,
        },
        ecological_metrics={
            "ecological_health": 0.25,
            "biodiversity_index": 0.15,
            "water_cycle_health": 0.30,
            "air_quality_impact": 0.40,
        },
        dependencies=industrial_deps,
    )

    # -- Regenerative polyculture --
    regen_deps = [
        Dependency(
            name="groundwater",
            type=DependencyType.CLEAN_WATER,
            current_cost=30,
            hidden_subsidy=20,
            degradation_rate=-0.05,
            alternative_cost=30,
            measurement_method="aquifer drawdown rate (m/yr)"
        ),
        Dependency(
            name="air_quality",
            type=DependencyType.CLEAN_AIR,
            current_cost=0,
            hidden_subsidy=10,
            degradation_rate=-0.02,
            alternative_cost=10,
            measurement_method="PM2.5 / NOx emissions (kg/ha/yr)"
        ),
        Dependency(
            name="open_seed",
            type=DependencyType.GENETIC_IP,
            current_cost=40,
            hidden_subsidy=10,
            degradation_rate=-0.03,
            alternative_cost=40,
            measurement_method="royalty + germplasm narrowing index"
        ),
    ]
    regenerative = create_system(
        production_metrics={
            "output_yield": 700,
            "input_energy": 150,
            "soil_trend": 0.3,
            "nutrient_density": 0.75,
            "water_use": 300,
            "fertilizer_use": 20,
            "pesticide_use": 0,
        },
        ecological_metrics={
            "ecological_health": 0.85,
            "biodiversity_index": 0.80,
            "water_cycle_health": 0.80,
            "air_quality_impact": 0.90,
        },
        dependencies=regen_deps,
    )

    return {"industrial_monoculture": industrial, "regenerative_polyculture": regenerative}


def _format_report(results: Dict[str, Dict[str, Any]]) -> str:
    """Format comparison results as a human-readable report."""
    lines: List[str] = []
    sep = "-" * 72

    lines.append(sep)
    lines.append("  EXPANDED FIELD SYSTEM — Dependency Accounting Comparison")
    lines.append(sep)

    for sys_name, metrics in results.items():
        lines.append("")
        lines.append(f"  System: {sys_name}")
        lines.append(f"  {'─' * 40}")
        lines.append(f"    True efficiency        : {metrics['true_efficiency']:.4f}")
        lines.append(f"    System health index    : {metrics['system_health']:.4f}")
        lines.append(f"    Externalization ratio  : {metrics['externalization_ratio']:.2%}")
        lines.append(f"    Total hidden subsidy   : {metrics['total_hidden_subsidy']:.1f}")
        lines.append(f"    Total true cost        : {metrics['total_true_cost']:.1f}")
        lines.append(f"    Critical risks         : {metrics['critical_risks']}")
        lines.append(f"    Total risks            : {metrics['total_risks']}")

        lines.append("")
        lines.append(f"    Dependencies:")
        for dep_name, dep_info in metrics["dependency_details"].items():
            lines.append(f"      {dep_name} ({dep_info['type']})")
            lines.append(f"        apparent={dep_info['apparent_cost']:.1f}  "
                         f"hidden={dep_info['hidden_subsidy']:.1f}  "
                         f"true={dep_info['true_cost']:.1f}  "
                         f"degrade={dep_info['degradation_rate']:.2f}  "
                         f"sustain={dep_info['sustainability']:.2f}")

    lines.append("")
    lines.append(sep)
    return "\n".join(lines)


def main():
    parser = argparse.ArgumentParser(
        description=(
            "Full dependency accounting for agricultural / production systems. "
            "Computes true costs, system health, externalization ratios, and "
            "dependency risk reports."
        )
    )
    parser.add_argument(
        "--demo",
        action="store_true",
        help="Run a demo comparing industrial monoculture vs. regenerative polyculture."
    )
    parser.add_argument(
        "--json",
        action="store_true",
        dest="json_output",
        help="Emit results as JSON instead of a human-readable report."
    )
    args = parser.parse_args()

    if not args.demo:
        parser.print_help()
        print("\n  Tip: use --demo to run an example comparison.")
        sys.exit(0)

    systems = _build_demo_systems()
    results = compare_systems(systems)

    if args.json_output:
        print(json.dumps(results, indent=2))
    else:
        print(_format_report(results))


if __name__ == "__main__":
    main()
