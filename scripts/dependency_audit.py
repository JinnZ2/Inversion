#!/usr/bin/env python3
"""
Dependency Audit Framework
==========================

Maps structural vulnerabilities, hidden subsidies, and systemic risks
within dependency networks.  Models each dependency as an auditable entry
with current cost, hidden subsidy, true cost, degradation rate, and
substitution feasibility.  Produces a structured report with vulnerability
index, sovereignty score, and actionable recommendations.

Metrics
-------
- **Externalization ratio** -- hidden subsidy / true cost across all
  dependencies.  Indicates what fraction of real cost is invisible to
  the operating entity.
- **Vulnerability index** (0-1) -- weighted sum of risk levels scaled
  by substitution difficulty (1 - feasibility).  Higher values indicate
  greater systemic fragility.
- **Sovereignty score** (0-1) -- weighted by dependency source type
  (commons > social capital > natural capital > public infra > private
  monopoly) and degradation rate.  Higher values indicate more
  autonomous control over critical inputs.

References
----------
- Meadows, D. (2008). *Thinking in Systems*.
- Ostrom, E. (1990). *Governing the Commons*.
- Raworth, K. (2017). *Doughnut Economics* -- hidden subsidies and
  externalized costs.
- Shannon, C. E. (1948). A Mathematical Theory of Communication --
  entropy as uncertainty measure applied to risk weighting.

Usage
-----
    python3 scripts/dependency_audit.py --demo
    python3 scripts/dependency_audit.py --demo --json
    python3 scripts/dependency_audit.py --demo --compare
"""

from dataclasses import dataclass, field
from typing import Dict, List, Any, Optional
from enum import Enum
from datetime import datetime
import argparse
import json
import math


# ------------------
# Audit Core Structures
# ------------------

class DependencyRisk(Enum):
    """Risk levels for dependencies."""
    CRITICAL = "critical"       # < 10 years remaining
    HIGH = "high"               # 10-20 years remaining
    MODERATE = "moderate"       # 20-50 years remaining
    LOW = "low"                 # > 50 years remaining
    IMPROVING = "improving"     # Negative degradation (building)


class DependencySource(Enum):
    """Where the dependency comes from."""
    PUBLIC_INFRASTRUCTURE = "public_infrastructure"
    PRIVATE_MONOPOLY = "private_monopoly"
    COMMONS = "commons"
    NATURAL_CAPITAL = "natural_capital"
    SOCIAL_CAPITAL = "social_capital"


@dataclass
class DependencyAuditEntry:
    """Complete audit record for a single dependency."""
    name: str
    source: DependencySource
    current_cost: float
    hidden_subsidy: float
    true_cost: float
    degradation_rate: float
    years_remaining: float
    risk_level: DependencyRisk
    alternative_available: bool
    alternative_cost: float
    substitution_feasibility: float   # 0-1
    measurement_method: str
    data_quality: float               # 0-1
    last_measured: datetime
    trend_history: List[float] = field(default_factory=list)

    def update_risk_level(self):
        """Update risk level based on years remaining."""
        if self.degradation_rate <= 0:
            self.risk_level = DependencyRisk.IMPROVING
        elif self.years_remaining < 10:
            self.risk_level = DependencyRisk.CRITICAL
        elif self.years_remaining < 20:
            self.risk_level = DependencyRisk.HIGH
        elif self.years_remaining < 50:
            self.risk_level = DependencyRisk.MODERATE
        else:
            self.risk_level = DependencyRisk.LOW


@dataclass
class SystemDependencyAudit:
    """Complete audit of all system dependencies."""
    system_name: str
    audit_date: datetime
    dependencies: Dict[str, DependencyAuditEntry]

    def total_hidden_subsidy(self) -> float:
        return sum(d.hidden_subsidy for d in self.dependencies.values())

    def total_true_cost(self) -> float:
        return sum(d.true_cost for d in self.dependencies.values())

    def externalization_ratio(self) -> float:
        total = self.total_true_cost()
        return self.total_hidden_subsidy() / total if total > 0 else 0

    def critical_dependencies(self) -> List[DependencyAuditEntry]:
        return [d for d in self.dependencies.values()
                if d.risk_level == DependencyRisk.CRITICAL]

    def vulnerability_index(self) -> float:
        """
        System vulnerability (0-1).
        Weighted by risk level and substitution difficulty.
        """
        weights = {
            DependencyRisk.CRITICAL: 1.0,
            DependencyRisk.HIGH: 0.7,
            DependencyRisk.MODERATE: 0.4,
            DependencyRisk.LOW: 0.1,
            DependencyRisk.IMPROVING: 0.0
        }
        total_risk = sum(
            weights[d.risk_level] * (1 - d.substitution_feasibility)
            for d in self.dependencies.values()
        )
        max_risk = len(self.dependencies) * 1.0
        return min(1.0, total_risk / max_risk) if max_risk > 0 else 0

    def sovereignty_score(self) -> float:
        """
        System sovereignty (0-1).
        Higher = more control over own dependencies.
        """
        source_weights = {
            DependencySource.COMMONS: 1.0,
            DependencySource.SOCIAL_CAPITAL: 0.9,
            DependencySource.NATURAL_CAPITAL: 0.7,
            DependencySource.PUBLIC_INFRASTRUCTURE: 0.4,
            DependencySource.PRIVATE_MONOPOLY: 0.1
        }
        total_score = sum(
            source_weights[d.source] * (1 - d.degradation_rate if d.degradation_rate > 0 else 1)
            for d in self.dependencies.values()
        )
        max_score = len(self.dependencies) * 1.0
        return total_score / max_score if max_score > 0 else 0

    def generate_report(self) -> Dict[str, Any]:
        """Generate structured audit report."""
        return {
            "system_name": self.system_name,
            "audit_date": self.audit_date.isoformat(),
            "summary": {
                "total_dependencies": len(self.dependencies),
                "total_hidden_subsidy": self.total_hidden_subsidy(),
                "total_true_cost": self.total_true_cost(),
                "externalization_ratio": self.externalization_ratio(),
                "critical_dependencies": len(self.critical_dependencies()),
                "vulnerability_index": self.vulnerability_index(),
                "sovereignty_score": self.sovereignty_score()
            },
            "dependencies": {
                name: {
                    "source": d.source.value,
                    "current_cost": d.current_cost,
                    "hidden_subsidy": d.hidden_subsidy,
                    "true_cost": d.true_cost,
                    "degradation_rate": d.degradation_rate,
                    "years_remaining": d.years_remaining,
                    "risk_level": d.risk_level.value,
                    "alternative_available": d.alternative_available,
                    "substitution_feasibility": d.substitution_feasibility,
                    "data_quality": d.data_quality
                }
                for name, d in self.dependencies.items()
            },
            "vulnerabilities": [
                {
                    "dependency": name,
                    "risk": d.risk_level.value,
                    "years": d.years_remaining,
                    "substitution": d.substitution_feasibility
                }
                for name, d in self.dependencies.items()
                if d.risk_level in [DependencyRisk.CRITICAL, DependencyRisk.HIGH]
            ],
            "recommendations": self._generate_recommendations()
        }

    def _generate_recommendations(self) -> List[str]:
        """Generate audit recommendations from data."""
        recommendations = []

        for dep in self.critical_dependencies():
            recommendations.append(
                f"CRITICAL: {dep.name} -- {dep.years_remaining:.0f} years remaining. "
                f"Alternative at {dep.alternative_cost:.0f} available."
            )

        if self.externalization_ratio() > 0.5:
            recommendations.append(
                f"Externalization ratio at {self.externalization_ratio():.0%}. "
                f"Internalization required for true cost visibility."
            )

        if self.sovereignty_score() < 0.3:
            recommendations.append(
                "Low sovereignty score -- high private monopoly control. "
                "Transition to commons-based alternatives recommended."
            )

        for name, dep in self.dependencies.items():
            if dep.data_quality < 0.5:
                recommendations.append(
                    f"Low data quality for {name} ({dep.data_quality:.0%}). "
                    f"Measurement improvement needed."
                )

        return recommendations


# ------------------
# Audit Factory
# ------------------

def create_audit(
    system_name: str,
    entries: List[DependencyAuditEntry],
    audit_date: Optional[datetime] = None
) -> SystemDependencyAudit:
    """
    Build an audit from a list of entries.

    Parameters
    ----------
    system_name : str
    entries : list[DependencyAuditEntry]
    audit_date : datetime, optional (defaults to now)

    Returns
    -------
    SystemDependencyAudit
    """
    if audit_date is None:
        audit_date = datetime.now()

    dependencies = {}
    for entry in entries:
        entry.update_risk_level()
        dependencies[entry.name] = entry

    return SystemDependencyAudit(
        system_name=system_name,
        audit_date=audit_date,
        dependencies=dependencies
    )


def compare_audits(
    audits: Dict[str, SystemDependencyAudit]
) -> Dict[str, Dict[str, Any]]:
    """
    Compare N audits side by side.

    Returns
    -------
    dict keyed by audit name -> summary metrics
    """
    results = {}
    for name, audit in audits.items():
        report = audit.generate_report()
        results[name] = report["summary"]
    return results


# ------------------
# Demo Data
# ------------------

def _build_demo_entries() -> List[DependencyAuditEntry]:
    """Return a set of illustrative dependency audit entries."""
    now = datetime.now()
    return [
        DependencyAuditEntry(
            name="Groundwater",
            source=DependencySource.NATURAL_CAPITAL,
            current_cost=50.0,
            hidden_subsidy=200.0,
            true_cost=250.0,
            degradation_rate=0.03,
            years_remaining=15.0,
            risk_level=DependencyRisk.HIGH,
            alternative_available=True,
            alternative_cost=400.0,
            substitution_feasibility=0.4,
            measurement_method="USGS well-level monitoring",
            data_quality=0.8,
            last_measured=now,
        ),
        DependencyAuditEntry(
            name="Grid Electricity",
            source=DependencySource.PRIVATE_MONOPOLY,
            current_cost=120.0,
            hidden_subsidy=80.0,
            true_cost=200.0,
            degradation_rate=0.01,
            years_remaining=40.0,
            risk_level=DependencyRisk.MODERATE,
            alternative_available=True,
            alternative_cost=180.0,
            substitution_feasibility=0.7,
            measurement_method="EIA capacity factor data",
            data_quality=0.9,
            last_measured=now,
        ),
        DependencyAuditEntry(
            name="Topsoil",
            source=DependencySource.NATURAL_CAPITAL,
            current_cost=0.0,
            hidden_subsidy=500.0,
            true_cost=500.0,
            degradation_rate=0.05,
            years_remaining=8.0,
            risk_level=DependencyRisk.CRITICAL,
            alternative_available=False,
            alternative_cost=1200.0,
            substitution_feasibility=0.1,
            measurement_method="NRCS soil survey",
            data_quality=0.6,
            last_measured=now,
        ),
        DependencyAuditEntry(
            name="Community Knowledge",
            source=DependencySource.SOCIAL_CAPITAL,
            current_cost=0.0,
            hidden_subsidy=150.0,
            true_cost=150.0,
            degradation_rate=-0.02,
            years_remaining=100.0,
            risk_level=DependencyRisk.IMPROVING,
            alternative_available=False,
            alternative_cost=0.0,
            substitution_feasibility=0.0,
            measurement_method="Participatory assessment",
            data_quality=0.4,
            last_measured=now,
        ),
        DependencyAuditEntry(
            name="Municipal Water Treatment",
            source=DependencySource.PUBLIC_INFRASTRUCTURE,
            current_cost=30.0,
            hidden_subsidy=70.0,
            true_cost=100.0,
            degradation_rate=0.02,
            years_remaining=25.0,
            risk_level=DependencyRisk.MODERATE,
            alternative_available=True,
            alternative_cost=90.0,
            substitution_feasibility=0.5,
            measurement_method="EPA compliance reports",
            data_quality=0.85,
            last_measured=now,
        ),
    ]


def _build_demo_comparison() -> Dict[str, SystemDependencyAudit]:
    """Build three scenario audits for side-by-side comparison."""
    now = datetime.now()
    base_entries = _build_demo_entries()

    baseline = create_audit("Baseline", base_entries, audit_date=now)

    # Degraded scenario: double degradation rates, halve years remaining
    degraded_entries = []
    for e in _build_demo_entries():
        e.degradation_rate = abs(e.degradation_rate) * 2
        e.years_remaining = max(1.0, e.years_remaining / 2)
        degraded_entries.append(e)
    degraded = create_audit("Degraded", degraded_entries, audit_date=now)

    # Resilient scenario: negative or zero degradation, high substitution
    resilient_entries = []
    for e in _build_demo_entries():
        e.degradation_rate = min(0, e.degradation_rate)
        e.substitution_feasibility = min(1.0, e.substitution_feasibility + 0.3)
        e.years_remaining = e.years_remaining * 2
        resilient_entries.append(e)
    resilient = create_audit("Resilient", resilient_entries, audit_date=now)

    return {"Baseline": baseline, "Degraded": degraded, "Resilient": resilient}


# ------------------
# CLI Presentation
# ------------------

def _print_report(report: Dict[str, Any]) -> None:
    """Pretty-print a single audit report to stdout."""
    s = report["summary"]
    print(f"=== Dependency Audit: {report['system_name']} ===")
    print(f"Date: {report['audit_date']}")
    print()
    print("Summary")
    print("-" * 40)
    print(f"  Total dependencies:      {s['total_dependencies']}")
    print(f"  Total hidden subsidy:    {s['total_hidden_subsidy']:.2f}")
    print(f"  Total true cost:         {s['total_true_cost']:.2f}")
    print(f"  Externalization ratio:   {s['externalization_ratio']:.2%}")
    print(f"  Critical dependencies:   {s['critical_dependencies']}")
    print(f"  Vulnerability index:     {s['vulnerability_index']:.4f}")
    print(f"  Sovereignty score:       {s['sovereignty_score']:.4f}")
    print()

    print("Dependencies")
    print("-" * 40)
    for name, d in report["dependencies"].items():
        print(f"  {name}")
        print(f"    Source:          {d['source']}")
        print(f"    Current cost:    {d['current_cost']:.2f}")
        print(f"    Hidden subsidy:  {d['hidden_subsidy']:.2f}")
        print(f"    True cost:       {d['true_cost']:.2f}")
        print(f"    Degradation:     {d['degradation_rate']:.4f}")
        print(f"    Years remaining: {d['years_remaining']:.1f}")
        print(f"    Risk level:      {d['risk_level']}")
        print(f"    Substitution:    {d['substitution_feasibility']:.2f}")
        print(f"    Data quality:    {d['data_quality']:.2f}")
        print()

    if report["vulnerabilities"]:
        print("Vulnerabilities")
        print("-" * 40)
        for v in report["vulnerabilities"]:
            print(f"  {v['dependency']:30s}  risk={v['risk']:10s}  "
                  f"years={v['years']:.0f}  substitution={v['substitution']:.2f}")
        print()

    if report["recommendations"]:
        print("Recommendations")
        print("-" * 40)
        for rec in report["recommendations"]:
            print(f"  - {rec}")
        print()


def _print_comparison(comparison: Dict[str, Dict[str, Any]]) -> None:
    """Pretty-print a side-by-side comparison table."""
    print("=== Audit Comparison ===")
    print()
    headers = list(comparison.keys())
    col_w = max(len(h) for h in headers) + 2
    metric_w = 28

    # Header row
    print(f"{'Metric':<{metric_w}}", end="")
    for h in headers:
        print(f"{h:>{col_w}}", end="")
    print()
    print("-" * (metric_w + col_w * len(headers)))

    # Metric rows
    sample = next(iter(comparison.values()))
    for key in sample:
        print(f"{key:<{metric_w}}", end="")
        for h in headers:
            val = comparison[h][key]
            if isinstance(val, float):
                print(f"{val:>{col_w}.4f}", end="")
            else:
                print(f"{val:>{col_w}}", end="")
        print()
    print()


# ------------------
# Main / CLI
# ------------------

def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description=(
            "Dependency Audit Framework -- maps structural vulnerabilities, "
            "hidden subsidies, and systemic risks within dependency networks."
        )
    )
    parser.add_argument(
        "--demo",
        action="store_true",
        help="Run a demo audit with illustrative dependency data."
    )
    parser.add_argument(
        "--compare",
        action="store_true",
        help="Run three scenario comparison (baseline / degraded / resilient)."
    )
    parser.add_argument(
        "--json",
        action="store_true",
        dest="json_output",
        help="Emit output as JSON instead of human-readable text."
    )
    return parser


def main() -> None:
    parser = build_parser()
    args = parser.parse_args()

    if not args.demo and not args.compare:
        parser.print_help()
        return

    if args.compare:
        audits = _build_demo_comparison()
        if args.json_output:
            comparison = compare_audits(audits)
            print(json.dumps(comparison, indent=2))
        else:
            comparison = compare_audits(audits)
            _print_comparison(comparison)
            # Also print full reports
            for audit in audits.values():
                report = audit.generate_report()
                _print_report(report)
    elif args.demo:
        entries = _build_demo_entries()
        audit = create_audit("Demo System", entries)
        report = audit.generate_report()
        if args.json_output:
            print(json.dumps(report, indent=2))
        else:
            _print_report(report)


if __name__ == "__main__":
    main()
