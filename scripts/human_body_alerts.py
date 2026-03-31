# human_body_alerts.py

# Human biological sensing as a detection framework

# Generic: register sensors and interpretation rules, then run detection

from dataclasses import dataclass, field
from typing import Dict, List, Any, Optional, Callable

# —————————

# Biological Sensor

# —————————

@dataclass
class BiologicalSensor:
“”“A biological sensing capability.”””
name: str
organ_system: str
what_it_detects: List[str]
sensitivity_range: str
calibration_signals: List[str]   # symptoms indicating activation
reliability: float               # 0-1
tags: Dict[str, str] = field(default_factory=dict)

# —————————

# Symptom Rule

# —————————

@dataclass
class SymptomRule:
“”“Maps a symptom to possible environmental causes.”””
symptom: str
possible_causes: List[str]
sensor: str                      # which sensor produces this symptom

# —————————

# Threat Condition

# —————————

@dataclass
class ThreatCondition:
“””
Maps an environmental condition key to sensors that activate.
Used in detect_threat_matrix().
“””
condition_key: str               # e.g. “infrasound”, “chemical”
threshold: float                 # minimum value to trigger
sensor_name: str
symptom: str
interpretation: str
confidence_scale: float = 0.7    # multiplied by condition value

# —————————

# Sensor Registry

# —————————

class SensorRegistry:
“”“Registry of biological sensors. Populate via register().”””

```
def __init__(self):
    self.sensors: Dict[str, BiologicalSensor] = {}

def register(self, sensor: BiologicalSensor):
    self.sensors[sensor.name] = sensor

def all(self) -> List[BiologicalSensor]:
    return list(self.sensors.values())

def by_organ(self, organ_keyword: str) -> List[BiologicalSensor]:
    return [
        s for s in self.sensors.values()
        if organ_keyword.lower() in s.organ_system.lower()
    ]
```

# —————————

# Human Geometric Coupling

# —————————

class HumanGeometricCoupling:
“””
Maps environmental conditions → biological detections.
Pluggable via ThreatCondition and SymptomRule registries.
“””

```
def __init__(self):
    self.threat_conditions: List[ThreatCondition] = []
    self.symptom_rules: List[SymptomRule] = []

def add_threat_condition(self, condition: ThreatCondition):
    self.threat_conditions.append(condition)

def add_symptom_rule(self, rule: SymptomRule):
    self.symptom_rules.append(rule)

def detect_threat_matrix(
    self, environmental_conditions: Dict[str, float]
) -> Dict[str, Any]:
    """
    Given environmental condition values, return which sensors
    activate and what they indicate.
    """
    detections = []

    for tc in self.threat_conditions:
        value = environmental_conditions.get(tc.condition_key, 0)
        if value >= tc.threshold:
            detections.append({
                "sensor": tc.sensor_name,
                "symptom": tc.symptom,
                "interpretation": tc.interpretation,
                "confidence": tc.confidence_scale * min(1.0, value),
            })

    # Integrated threat (multiple sensors activating)
    if len(detections) > 2:
        avg_conf = sum(d["confidence"] for d in detections) / len(detections)
        detections.append({
            "sensor": "integrated",
            "symptom": "Multiple signals — heightened awareness",
            "interpretation": "Multiple environmental signals indicate threat",
            "confidence": min(1.0, avg_conf * 1.2),
        })

    overall = (
        sum(d["confidence"] for d in detections) / len(detections)
        if detections else 0
    )

    return {
        "detections": detections,
        "overall_threat_level": min(1.0, overall),
        "sensors_activated": list(set(d["sensor"] for d in detections)),
    }

def interpret_symptoms(
    self, symptoms: List[str]
) -> List[Dict[str, Any]]:
    """
    Given reported symptoms, return possible environmental causes.
    """
    results = []
    for symptom in symptoms:
        matching = [r for r in self.symptom_rules if r.symptom == symptom]
        for rule in matching:
            results.append({
                "symptom": rule.symptom,
                "possible_causes": rule.possible_causes,
                "sensor": rule.sensor,
            })
    return results
```
