# mineral_mulch_sim.py

# Simulate stone-mulch microclimate effects on root zone:

# thermal condensation, pH buffering, biological activity,

# multi-layer mineral decay, thermal shock, cumulative stress,

# lateral frost protection

# All parameters configurable — no hardcoded location constants.

import math
from dataclasses import dataclass, field
from typing import Dict, List, Any, Optional

# —————————

# Site and Material Parameters

# —————————

@dataclass
class SiteParams:
“”“Environmental baseline for the site.”””
soil_ph: float = 4.5
soil_moisture: float = 0.15         # fraction (0-1)
mean_temp_c: float = 11.0           # daily mean
temp_amplitude_c: float = 13.0      # half-range of daily swing
temp_peak_hour: int = 14            # hour of day peak
root_temp_initial_c: float = 2.0    # stable root-zone temperature
root_death_temp_c: float = -15.0    # lethal root threshold

@dataclass
class StoneLayer:
“”“Properties of a single stone layer.”””
name: str
albedo: float               # 0-1, reflectivity
dissolution_rate: float     # pH units buffered per time step per pH deficit
porosity: float             # 0-1
weathering_rate: float      # fraction lost per year per unit weather severity
insulation_factor: float    # 0-1, thermal resistance contribution

# —————————

# Daily Thermal Cycle

# —————————

def hourly_temperature(hour: int, mean: float, amplitude: float, peak_hour: int = 14) -> float:
“”“Sinusoidal temperature model.”””
return mean + amplitude * math.sin((hour - peak_hour + 6) * math.pi / 12)

def thermal_condensation(
air_temp: float,
albedo: float,
) -> tuple:
“””
Stone surface temperature and condensation estimate.

```
Returns (stone_temp, condensation_mm)
"""
stone_temp = air_temp * (1 - albedo)
condensation = max(0, (air_temp - stone_temp) * 0.01)
return stone_temp, condensation
```

def simulate_daily_cycle(
site: SiteParams,
layer: StoneLayer,
hours: int = 24,
report_interval: int = 4,
) -> Dict[str, Any]:
“””
Run one 24-hour cycle tracking temperature, condensation, pH, moisture.

```
Returns dict with hourly arrays and final state.
"""
ph = site.soil_ph
moisture = site.soil_moisture
log = []

for hour in range(hours):
    air_temp = hourly_temperature(hour, site.mean_temp_c, site.temp_amplitude_c, site.temp_peak_hour)
    stone_temp, dew = thermal_condensation(air_temp, layer.albedo)
    moisture += dew

    # pH buffering: dissolution proportional to acid deficit
    if ph < 7.0:
        ph += layer.dissolution_rate / (ph + 0.1)

    log.append({
        "hour": hour,
        "air_temp": round(air_temp, 2),
        "stone_temp": round(stone_temp, 2),
        "condensation": round(dew, 5),
        "ph": round(ph, 3),
        "moisture": round(moisture, 5),
    })

return {
    "log": log,
    "final_ph": ph,
    "final_moisture": moisture,
    "total_condensation": sum(e["condensation"] for e in log),
}
```

# —————————

# Biological Activity Gate

# —————————

@dataclass
class BioState:
“”“Biological activity state.”””
microbe_efficiency: float = 0.0   # 0-1
insect_density: float = 0.0       # relative

def update_biology(
state: BioState,
ph: float,
moisture: float,
temp: float,
ph_optimum: float = 7.0,
ph_range: float = 3.0,
moisture_threshold: float = 0.18,
temp_low: float = 10.0,
temp_high: float = 22.0,
growth_rate: float = 0.05,
decline_rate: float = 0.02,
) -> BioState:
“””
Update biological activity based on current conditions.
Microbe efficiency peaks when pH approaches optimum.
Insect density grows when temperature and moisture are favorable.
“””
efficiency = max(0, 1 - abs(ph_optimum - ph) / ph_range)

```
if temp_low < temp < temp_high and moisture > moisture_threshold:
    density = state.insect_density + growth_rate * efficiency
else:
    density = state.insect_density - decline_rate

return BioState(
    microbe_efficiency=round(efficiency, 4),
    insect_density=round(max(0, density), 4),
)
```

# —————————

# Multi-Layer Mineral Decay (Long-Term)

# —————————

@dataclass
class MineralState:
“”“State of multi-layer mineral reserves.”””
buffer_reserve: float = 100.0    # reactive layer (e.g., limestone) %
armor_integrity: float = 100.0   # protective cap (e.g., granite) %
soil_ph: float = 4.5
biotic_capital: float = 0.0      # accumulated biological capacity

def step_mineral_year(
state: MineralState,
weather_severity: float = 1.0,
buffer_layer: Optional[StoneLayer] = None,
armor_layer: Optional[StoneLayer] = None,
) -> MineralState:
“””
Advance mineral state by one year.

```
buffer_layer dissolves to raise pH.
armor_layer weathers slowly, protecting buffer.
"""
bl = buffer_layer or StoneLayer("buffer", 0.4, 0.005, 0.2, 0.001, 0.4)
al = armor_layer or StoneLayer("armor", 0.5, 0.0001, 0.05, 0.001, 0.5)

# Armor weathering
armor = max(0, state.armor_integrity - al.weathering_rate * weather_severity * 100)

# Buffer dissolution (proportional to pH deficit)
ph_deficit = max(0, 7.0 - state.soil_ph)
dissolution = 0.05 * ph_deficit
buffer = max(0, state.buffer_reserve - dissolution)

# pH change
if state.buffer_reserve > 0:
    ph = state.soil_ph + dissolution * 0.8
else:
    ph = state.soil_ph - 0.02  # slow re-acidification

# Biotic capital accumulates as pH improves
bio = state.biotic_capital + 0.1 * (ph / 5.0)

return MineralState(
    buffer_reserve=round(buffer, 2),
    armor_integrity=round(armor, 2),
    soil_ph=round(min(7.0, ph), 3),
    biotic_capital=round(bio, 3),
)
```

def simulate_years(
initial: Optional[MineralState] = None,
years: int = 15,
weather_severity: float = 1.0,
buffer_layer: Optional[StoneLayer] = None,
armor_layer: Optional[StoneLayer] = None,
) -> List[Dict[str, Any]]:
“”“Run multi-year mineral decay simulation.”””
state = initial or MineralState()
log = []
for y in range(1, years + 1):
state = step_mineral_year(state, weather_severity, buffer_layer, armor_layer)
log.append({
“year”: y,
“buffer_reserve”: state.buffer_reserve,
“armor_integrity”: state.armor_integrity,
“soil_ph”: state.soil_ph,
“biotic_capital”: state.biotic_capital,
})
return log

# —————————

# Thermal Shock

# —————————

def thermal_shock(
root_temp: float,
ambient_temp: float,
duration_hours: int,
insulation_factor: float = 0.85,
death_threshold: float = -15.0,
) -> Dict[str, Any]:
“””
Simulate thermal shock propagation through insulation.

```
Returns final root temp, survival status, and hourly trace.
"""
trace = []
alive = True
t = root_temp

for hour in range(duration_hours):
    heat_loss = (t - ambient_temp) * (1 - insulation_factor) * 0.05
    t -= heat_loss
    trace.append(round(t, 3))
    if t <= death_threshold:
        alive = False
        break

return {
    "initial_root_temp": root_temp,
    "ambient_temp": ambient_temp,
    "duration_hours": duration_hours,
    "final_root_temp": round(t, 3),
    "alive": alive,
    "hours_survived": len(trace),
    "trace": trace,
}
```

# —————————

# Cumulative Stress / Recovery

# —————————

@dataclass
class StressState:
“”“Cumulative stress and health state.”””
health: float = 100.0
entropy_load: float = 0.0

def step_stress_year(
state: StressState,
shock_events: int,
insulation_factor: float = 0.85,
temp_delta: float = 42.0,
damage_threshold: float = 20.0,
damage_rate: float = 0.5,
summer_recovery: float = 15.0,
health_regen: float = 3.0,
) -> StressState:
“””
Apply shock events and summer recovery for one year.
“””
entropy = state.entropy_load
health = state.health

```
for _ in range(shock_events):
    stress = temp_delta * (1 - insulation_factor)
    entropy += stress
    if entropy > damage_threshold:
        health -= (entropy - damage_threshold) * damage_rate

# Summer recovery
entropy = max(0, entropy - summer_recovery)
health = min(100, health + health_regen)

return StressState(
    health=round(max(0, health), 2),
    entropy_load=round(entropy, 2),
)
```

def simulate_stress_years(
years: int = 15,
initial: Optional[StressState] = None,
event_schedule: Optional[List[int]] = None,
insulation_factor: float = 0.85,
) -> List[Dict[str, Any]]:
“””
Multi-year cumulative stress simulation.

```
event_schedule: shock events per year (default: increasing).
"""
state = initial or StressState()
if event_schedule is None:
    event_schedule = [1 + (y // 4) for y in range(years)]

log = []
for y in range(years):
    events = event_schedule[y] if y < len(event_schedule) else event_schedule[-1]
    state = step_stress_year(state, events, insulation_factor)
    log.append({
        "year": y + 1,
        "events": events,
        "health": state.health,
        "entropy_load": state.entropy_load,
        "status": "alive" if state.health > 0 else "dead",
    })
    if state.health <= 0:
        break
return log
```

# —————————

# Lateral Frost Protection

# —————————

def frost_protection_hours(
spread_diameter_ft: float,
external_temp_c: float = -45.0,
insulation_bonus: float = 0.4,
reference_temp_c: float = -10.0,
) -> float:
“””
Estimate hours until frost penetrates to root center.
Time scales with (effective_radius)² / temperature severity.
“””
radius_cm = (spread_diameter_ft / 2) * 30.48
effective_resistance = radius_cm * (1 + insulation_bonus)
severity = abs(external_temp_c / reference_temp_c)
return (effective_resistance ** 2) / (100 * severity)

def compare_spreads(
diameters_ft: List[float],
external_temp_c: float = -45.0,
insulation_bonus: float = 0.4,
) -> List[Dict[str, float]]:
“”“Compare frost protection across different spread diameters.”””
return [
{
“diameter_ft”: d,
“safe_hours”: round(frost_protection_hours(d, external_temp_c, insulation_bonus), 1),
}
for d in diameters_ft
]
