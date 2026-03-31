# operational_risk_monitor.py

# Weighted risk scoring, price divergence detection, field observation analysis

# Generic framework: configure weights and thresholds for any domain

from dataclasses import dataclass, field
from typing import Dict, List, Any, Optional

# —————————

# Weighted Risk Scorer

# —————————

@dataclass
class RiskProfile:
“”“Configurable weighted risk scorer.”””
weights: Dict[str, float]
# metric_name → weight (should sum to ~1.0)

```
def score(self, metrics: Dict[str, float]) -> float:
    """
    Weighted sum of normalized metrics (each 0-1).
    Returns 0-1 composite risk score.
    """
    total = sum(
        metrics.get(k, 0) * w
        for k, w in self.weights.items()
    )
    return round(min(1.0, max(0, total)), 3)

def classify(
    self,
    metrics: Dict[str, float],
    thresholds: Optional[Dict[str, float]] = None,
) -> Dict[str, Any]:
    """
    Score and classify into risk bands.

    Parameters
    ----------
    thresholds : dict, optional
        {"critical": 0.7, "warning": 0.4}
    """
    if thresholds is None:
        thresholds = {"critical": 0.7, "warning": 0.4}

    s = self.score(metrics)
    if s >= thresholds.get("critical", 0.7):
        level = "critical"
    elif s >= thresholds.get("warning", 0.4):
        level = "warning"
    else:
        level = "nominal"

    return {"score": s, "level": level, "metrics": metrics}
```

# —————————

# Price Divergence Detector

# —————————

def price_divergence(
reference_price: float,
actual_price: float,
critical_threshold: float = 0.30,
) -> Dict[str, Any]:
“””
Detect when actual price diverges significantly from reference.
Large negative divergence (actual << reference) may indicate
substitution with lower-quality inputs.

```
Returns
-------
dict with divergence ratio and classification
"""
if reference_price <= 0:
    return {"divergence": 0, "level": "invalid", "note": "reference_price <= 0"}

divergence = (reference_price - actual_price) / reference_price

if divergence > critical_threshold:
    level = "critical"
elif divergence > critical_threshold * 0.5:
    level = "warning"
else:
    level = "nominal"

return {
    "reference_price": reference_price,
    "actual_price": actual_price,
    "divergence": round(divergence, 3),
    "level": level,
}
```

# —————————

# Field Observation Scorer

# —————————

@dataclass
class FieldObservation:
“””
Weighted field observation risk assessment.
Each observation is 0-1 (0 = no concern, 1 = maximum concern).
“””
weights: Dict[str, float]
# observation_name → weight

```
def assess(
    self,
    observations: Dict[str, float],
    thresholds: Optional[Dict[str, float]] = None,
) -> Dict[str, Any]:
    """
    Score field observations and classify.
    """
    if thresholds is None:
        thresholds = {"critical": 0.7, "warning": 0.4}

    total = sum(
        observations.get(k, 0) * w
        for k, w in self.weights.items()
    )
    total = round(min(1.0, max(0, total)), 3)

    if total >= thresholds.get("critical", 0.7):
        level = "critical"
    elif total >= thresholds.get("warning", 0.4):
        level = "warning"
    else:
        level = "nominal"

    return {"score": total, "level": level, "observations": observations}
```

# —————————

# Redline Detector

# —————————

def redline_check(
metrics: Dict[str, float],
redline_rules: Optional[List[Dict[str, Any]]] = None,
) -> Dict[str, Any]:
“””
Check if a system has crossed critical thresholds.

```
Parameters
----------
metrics : dict
    metric_name → value (0-1 scale, direction depends on metric)
redline_rules : list of dicts, optional
    Each rule: {"name": str, "conditions": dict, "level": str}
    conditions: metric_name → {"above": float} or {"below": float}

Returns
-------
dict with triggered rules and overall status
"""
if redline_rules is None:
    # Default: infrastructure below 0.4 AND error above 0.6
    redline_rules = [
        {
            "name": "systemic_failure",
            "conditions": {
                "infrastructure_integrity": {"below": 0.4},
                "error_rate": {"above": 0.6},
            },
            "level": "critical",
        },
        {
            "name": "infrastructure_decay",
            "conditions": {
                "infrastructure_integrity": {"below": 0.5},
            },
            "level": "warning",
        },
        {
            "name": "high_error",
            "conditions": {
                "error_rate": {"above": 0.5},
            },
            "level": "warning",
        },
    ]

triggered = []
for rule in redline_rules:
    all_met = True
    for metric_name, condition in rule["conditions"].items():
        value = metrics.get(metric_name, 0)
        if "above" in condition and value <= condition["above"]:
            all_met = False
        if "below" in condition and value >= condition["below"]:
            all_met = False
    if all_met:
        triggered.append({"rule": rule["name"], "level": rule["level"]})

# Overall status: worst triggered level
if any(t["level"] == "critical" for t in triggered):
    overall = "critical"
elif any(t["level"] == "warning" for t in triggered):
    overall = "warning"
else:
    overall = "nominal"

return {"overall": overall, "triggered": triggered, "metrics": metrics}
```

# —————————

# Batch Audit

# —————————

def audit_batch(
entities: Dict[str, Dict[str, float]],
risk_profile: RiskProfile,
thresholds: Optional[Dict[str, float]] = None,
) -> List[Dict[str, Any]]:
“””
Run risk scoring across multiple entities.

```
Parameters
----------
entities : dict
    entity_name → {metric_name: value}
risk_profile : RiskProfile

Returns
-------
list of results sorted by score descending
"""
results = []
for name, metrics in entities.items():
    r = risk_profile.classify(metrics, thresholds)
    r["entity"] = name
    results.append(r)

results.sort(key=lambda x: -x["score"])
return results
```
