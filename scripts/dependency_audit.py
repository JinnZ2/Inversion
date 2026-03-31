# dependency_audit.py

# Dependency Audit Framework

# Maps structural vulnerabilities, hidden subsidies, and systemic risks

from dataclasses import dataclass, field
from typing import Dict, List, Any, Optional
from enum import Enum
from datetime import datetime
import math

# —————————

# Audit Core Structures

# —————————

class DependencyRisk(Enum):
“”“Risk levels for dependencies.”””
CRITICAL = “critical”       # < 10 years remaining
HIGH = “high”               # 10-20 years remaining
MODERATE = “moderate”       # 20-50 years remaining
LOW = “low”                 # > 50 years remaining
IMPROVING = “improving”     # Negative degradation (building)

class DependencySource(Enum):
“”“Where the dependency comes from.”””
PUBLIC_INFRASTRUCTURE = “public_infrastructure”
PRIVATE_MONOPOLY = “private_monopoly”
COMMONS = “commons”
NATURAL_CAPITAL = “natural_capital”
SOCIAL_CAPITAL = “social_capital”

@dataclass
class DependencyAuditEntry:
“”“Complete audit record for a single dependency.”””
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

```
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
```

@dataclass
class SystemDependencyAudit:
“”“Complete audit of all system dependencies.”””
system_name: str
audit_date: datetime
dependencies: Dict[str, DependencyAuditEntry]

```
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
            f"CRITICAL: {dep.name} — {dep.years_remaining:.0f} years remaining. "
            f"Alternative at {dep.alternative_cost:.0f} available."
        )

    if self.externalization_ratio() > 0.5:
        recommendations.append(
            f"Externalization ratio at {self.externalization_ratio():.0%}. "
            f"Internalization required for true cost visibility."
        )

    if self.sovereignty_score() < 0.3:
        recommendations.append(
            "Low sovereignty score — high private monopoly control. "
            "Transition to commons-based alternatives recommended."
        )

    for name, dep in self.dependencies.items():
        if dep.data_quality < 0.5:
            recommendations.append(
                f"Low data quality for {name} ({dep.data_quality:.0%}). "
                f"Measurement improvement needed."
            )

    return recommendations
```

# —————————

# Audit Factory

# —————————

def create_audit(
system_name: str,
entries: List[DependencyAuditEntry],
audit_date: Optional[datetime] = None
) -> SystemDependencyAudit:
“””
Build an audit from a list of entries.

```
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
```

def compare_audits(
audits: Dict[str, SystemDependencyAudit]
) -> Dict[str, Dict[str, Any]]:
“””
Compare N audits side by side.

```
Returns
-------
dict keyed by audit name → summary metrics
"""
results = {}
for name, audit in audits.items():
    report = audit.generate_report()
    results[name] = report["summary"]
return results
```
