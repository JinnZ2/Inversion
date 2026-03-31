# field_system.py

# Portable rule-field engine for regenerative system tracking

# Constraint layer + effective yield + ecological coupling + valuation

from typing import Dict, Any, Optional
import math

# —————————

# Defaults

# —————————

DEFAULTS = {
“soil_trend”: 0.0,
“water_retention”: 0.5,
“input_energy”: 1.0,
“output_yield”: 1.0,
“disturbance”: 0.0,
“waste_factor”: 0.3,
“nutrient_density”: 0.8,
}

BASELINES = {
“water_retention_min”: 0.4,
“energy_ratio_min”: 1.0,
“nutrient_density_min”: 0.7,
}

# —————————

# State Helpers

# —————————

def fill_state(state: Dict[str, Any]) -> Dict[str, float]:
“”“Fill missing values with defaults.”””
return {k: float(state.get(k, DEFAULTS[k])) for k in DEFAULTS}

def regen_capacity(state: Dict[str, float]) -> float:
“””
Regeneration capacity proxy.
Scales with soil health and water retention, penalized by disturbance.
“””
base = 1.0
soil_factor = 1.0 + state[“soil_trend”]
water_factor = state[“water_retention”]
disturbance_penalty = 1.0 - state[“disturbance”]
return base * soil_factor * water_factor * disturbance_penalty

# —————————

# Constraint Layer

# —————————

def constraints(state: Dict[str, float]) -> Dict[str, bool]:
“”“Non-negotiable system rules.”””
rc = regen_capacity(state)
energy_ratio = (
state[“output_yield”] / state[“input_energy”]
if state[“input_energy”] > 0 else 0
)
return {
“soil_positive”: state[“soil_trend”] >= 0,
“water_non_degrading”: state[“water_retention”] >= BASELINES[“water_retention_min”],
“no_overextraction”: state[“output_yield”] <= rc,
“energy_ratio”: energy_ratio >= BASELINES[“energy_ratio_min”],
“nutrient_adequate”: state[“nutrient_density”] >= BASELINES[“nutrient_density_min”],
}

def drift(state: Dict[str, float]) -> Dict[str, bool]:
“”“Which constraints are violated.”””
c = constraints(state)
return {k: not v for k, v in c.items()}

# —————————

# Suggestions

# —————————

def suggest(state: Dict[str, float]) -> Dict[str, Any]:
“”“Structured suggestions based on drift.”””
issues = drift(state)
actions = []
if issues.get(“soil_positive”):
actions.append(“Increase biomass input, reduce tillage/disturbance”)
if issues.get(“water_non_degrading”):
actions.append(“Improve water retention (mulch, contouring, infiltration)”)
if issues.get(“no_overextraction”):
actions.append(“Reduce yield pressure or increase regeneration capacity”)
if issues.get(“energy_ratio”):
actions.append(“Reduce external inputs or improve system efficiency”)
if issues.get(“nutrient_adequate”):
actions.append(“Increase soil biology, reduce monoculture pressure”)
return {“issues”: issues, “actions”: actions}

# —————————

# Scoring

# —————————

def score(state: Dict[str, float]) -> float:
“”“Fraction of constraints satisfied (0-1).”””
c = constraints(state)
return sum(c.values()) / len(c)

# —————————

# Effective Yield Accounting

# —————————

def effective_yield(state: Dict[str, float]) -> Dict[str, float]:
“””
True nourishment throughput accounting for waste and nutrient density.

```
Y_usable  = Y_gross × (1 - W_f)
Y_nutrient = Y_usable × N_d
Y_behavioral = Y_nutrient / N_d  (compensatory consumption)

The behavioral demand equation:
    Y_required = Y_target / ((1 - W_f) × N_d²)
"""
wf = state.get("waste_factor", DEFAULTS["waste_factor"])
nd = state.get("nutrient_density", DEFAULTS["nutrient_density"])
yg = state["output_yield"]

usable = yg * (1 - wf)
nutrient = usable * nd
# Compensatory: low density → eat more to meet needs
behavioral = nutrient / nd if nd > 0 else 0

# Amplification factor: how much extra production the system
# must generate to actually nourish (vs raw yield)
amplification = 1.0 / ((1 - wf) * nd * nd) if (wf < 1 and nd > 0) else float('inf')

return {
    "gross": yg,
    "usable": usable,
    "nutrient_adjusted": nutrient,
    "behavioral_demand": behavioral,
    "amplification_factor": amplification,
}
```

# —————————

# Ecological Coupling

# —————————

def ecological_amplification(
production_area: float,
ecological_area: float,
coupling_strength: float,
max_amplification: float = 2.0,
) -> Dict[str, float]:
“””
Model: effective yield = Y_adj × g(k)
where g(k) = 1 + α × k

```
Parameters
----------
production_area : float — acres under cultivation
ecological_area : float — acres of ecological support
coupling_strength : float — k, 0-1
max_amplification : float — α, maximum ecological multiplier

Returns
-------
dict with g(k), effective area ratio, and notes
"""
g = 1.0 + max_amplification * coupling_strength
effective_production = production_area * g
total_area = production_area + ecological_area

return {
    "production_area": production_area,
    "ecological_area": ecological_area,
    "coupling_strength": coupling_strength,
    "amplification_g": g,
    "effective_production_equivalent": effective_production,
    "total_area": total_area,
    "land_efficiency": effective_production / total_area if total_area > 0 else 0,
}
```

# —————————

# Valuation Distortion

# —————————

def valuation_distortion(
extractive_value: float,
internal_cost: float,
external_cost: float,
irreversibility_cost: float,
discount_rate: float = 0.05,
horizon_years: int = 30,
) -> Dict[str, float]:
“””
Market price vs thermodynamic reality.

```
P_market uses: (V_e - C_internal) / (1+r)^t
P_true uses:   (V_e - C_internal - C_external - C_irreversibility) / (1+r)^t

Returns ratio and gap.
"""
p_market = sum(
    (extractive_value - internal_cost) / ((1 + discount_rate) ** t)
    for t in range(horizon_years)
)
p_true = sum(
    (extractive_value - internal_cost - external_cost - irreversibility_cost)
    / ((1 + discount_rate) ** t)
    for t in range(horizon_years)
)

return {
    "market_value": max(0, p_market),
    "true_value": p_true,
    "distortion_ratio": p_market / p_true if p_true != 0 else float('inf'),
    "hidden_subsidy": max(0, p_market - p_true) if p_true < p_market else 0,
    "discount_rate": discount_rate,
    "horizon_years": horizon_years,
}
```

# —————————

# Full Report

# —————————

def report(state: Dict[str, Any]) -> Dict[str, Any]:
“”“Full evaluation pipeline.”””
s = fill_state(state)
return {
“state”: s,
“constraints”: constraints(s),
“drift”: drift(s),
“score”: score(s),
“suggestions”: suggest(s),
“effective_yield”: effective_yield(s),
“regen_capacity”: regen_capacity(s),
}
