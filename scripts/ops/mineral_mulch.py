#!/usr/bin/env python3
"""
mineral_mulch.py — Stone-mulch microclimate simulation for root-zone protection.

Purpose:
    Simulate the effects of stone mulch layers on root-zone microclimates,
    including thermal condensation, pH buffering via mineral dissolution,
    biological activity gating, multi-layer mineral decay over years,
    thermal shock propagation, cumulative stress/recovery cycles, and
    lateral frost protection scaling.

    All parameters are configurable — no hardcoded location constants.

Methodology:
    - Thermal cycle: sinusoidal daily temperature model with albedo-dependent
      stone surface cooling and dew-point condensation estimates.
    - pH buffering: dissolution rate proportional to acid deficit (pH < 7).
    - Biological activity: microbe efficiency as a function of pH proximity
      to optimum; insect density gated by temperature and moisture windows.
    - Mineral decay: two-layer model (reactive buffer + protective armor)
      with weathering and dissolution over multi-year timescales.
    - Thermal shock: exponential heat-loss model through insulative layers
      with lethal-threshold detection.
    - Cumulative stress: entropy-load accumulation from shock events with
      seasonal recovery and health tracking.
    - Frost protection: radial heat-diffusion scaling — time to frost
      penetration proportional to (effective radius)^2 / severity.

References:
    - Jury, W.A. & Horton, R. (2004). Soil Physics, 6th ed. Wiley.
    - Hillel, D. (2003). Introduction to Environmental Soil Physics. Academic Press.
    - Poesen, J. & Lavee, H. (1994). Rock fragments in top soils: significance
      and processes. Catena, 23(1-2), 1-28.
    - Kemper, W.D. et al. (1994). Stone cover and mulch effects on soil loss.
      Soil Technology, 7(2), 97-108.
"""

import argparse
import json
import math
import sys
from dataclasses import dataclass, field
from typing import Dict, List, Any, Optional

# ------------------
# Site and Material Parameters
# ------------------


@dataclass
class SiteParams:
    """Environmental baseline for the site."""
    soil_ph: float = 4.5
    soil_moisture: float = 0.15         # fraction (0-1)
    mean_temp_c: float = 11.0           # daily mean
    temp_amplitude_c: float = 13.0      # half-range of daily swing
    temp_peak_hour: int = 14            # hour of day peak
    root_temp_initial_c: float = 2.0    # stable root-zone temperature
    root_death_temp_c: float = -15.0    # lethal root threshold


@dataclass
class StoneLayer:
    """Properties of a single stone layer."""
    name: str
    albedo: float               # 0-1, reflectivity
    dissolution_rate: float     # pH units buffered per time step per pH deficit
    porosity: float             # 0-1
    weathering_rate: float      # fraction lost per year per unit weather severity
    insulation_factor: float    # 0-1, thermal resistance contribution


# ------------------
# Daily Thermal Cycle
# ------------------


def hourly_temperature(hour: int, mean: float, amplitude: float, peak_hour: int = 14) -> float:
    """Sinusoidal temperature model."""
    return mean + amplitude * math.sin((hour - peak_hour + 6) * math.pi / 12)


def thermal_condensation(
    air_temp: float,
    albedo: float,
) -> tuple:
    """
    Stone surface temperature and condensation estimate.

    Returns (stone_temp, condensation_mm)
    """
    stone_temp = air_temp * (1 - albedo)
    condensation = max(0, (air_temp - stone_temp) * 0.01)
    return stone_temp, condensation


def simulate_daily_cycle(
    site: SiteParams,
    layer: StoneLayer,
    hours: int = 24,
    report_interval: int = 4,
) -> Dict[str, Any]:
    """
    Run one 24-hour cycle tracking temperature, condensation, pH, moisture.

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


# ------------------
# Biological Activity Gate
# ------------------


@dataclass
class BioState:
    """Biological activity state."""
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
    """
    Update biological activity based on current conditions.
    Microbe efficiency peaks when pH approaches optimum.
    Insect density grows when temperature and moisture are favorable.
    """
    efficiency = max(0, 1 - abs(ph_optimum - ph) / ph_range)

    if temp_low < temp < temp_high and moisture > moisture_threshold:
        density = state.insect_density + growth_rate * efficiency
    else:
        density = state.insect_density - decline_rate

    return BioState(
        microbe_efficiency=round(efficiency, 4),
        insect_density=round(max(0, density), 4),
    )


# ------------------
# Multi-Layer Mineral Decay (Long-Term)
# ------------------


@dataclass
class MineralState:
    """State of multi-layer mineral reserves."""
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
    """
    Advance mineral state by one year.

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


def simulate_years(
    initial: Optional[MineralState] = None,
    years: int = 15,
    weather_severity: float = 1.0,
    buffer_layer: Optional[StoneLayer] = None,
    armor_layer: Optional[StoneLayer] = None,
) -> List[Dict[str, Any]]:
    """Run multi-year mineral decay simulation."""
    state = initial or MineralState()
    log = []
    for y in range(1, years + 1):
        state = step_mineral_year(state, weather_severity, buffer_layer, armor_layer)
        log.append({
            "year": y,
            "buffer_reserve": state.buffer_reserve,
            "armor_integrity": state.armor_integrity,
            "soil_ph": state.soil_ph,
            "biotic_capital": state.biotic_capital,
        })
    return log


# ------------------
# Thermal Shock
# ------------------


def thermal_shock(
    root_temp: float,
    ambient_temp: float,
    duration_hours: int,
    insulation_factor: float = 0.85,
    death_threshold: float = -15.0,
) -> Dict[str, Any]:
    """
    Simulate thermal shock propagation through insulation.

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


# ------------------
# Cumulative Stress / Recovery
# ------------------


@dataclass
class StressState:
    """Cumulative stress and health state."""
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
    """
    Apply shock events and summer recovery for one year.
    """
    entropy = state.entropy_load
    health = state.health

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


def simulate_stress_years(
    years: int = 15,
    initial: Optional[StressState] = None,
    event_schedule: Optional[List[int]] = None,
    insulation_factor: float = 0.85,
) -> List[Dict[str, Any]]:
    """
    Multi-year cumulative stress simulation.

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


# ------------------
# Lateral Frost Protection
# ------------------


def frost_protection_hours(
    spread_diameter_ft: float,
    external_temp_c: float = -45.0,
    insulation_bonus: float = 0.4,
    reference_temp_c: float = -10.0,
) -> float:
    """
    Estimate hours until frost penetrates to root center.
    Time scales with (effective_radius)^2 / temperature severity.
    """
    radius_cm = (spread_diameter_ft / 2) * 30.48
    effective_resistance = radius_cm * (1 + insulation_bonus)
    severity = abs(external_temp_c / reference_temp_c)
    return (effective_resistance ** 2) / (100 * severity)


def compare_spreads(
    diameters_ft: List[float],
    external_temp_c: float = -45.0,
    insulation_bonus: float = 0.4,
) -> List[Dict[str, float]]:
    """Compare frost protection across different spread diameters."""
    return [
        {
            "diameter_ft": d,
            "safe_hours": round(frost_protection_hours(d, external_temp_c, insulation_bonus), 1),
        }
        for d in diameters_ft
    ]


# ------------------
# CLI
# ------------------


def _print_table(rows: List[Dict[str, Any]], keys: Optional[List[str]] = None) -> None:
    """Print a list of dicts as a simple aligned table."""
    if not rows:
        return
    keys = keys or list(rows[0].keys())
    widths = {k: max(len(str(k)), *(len(str(r.get(k, ""))) for r in rows)) for k in keys}
    header = "  ".join(str(k).rjust(widths[k]) for k in keys)
    print(header)
    print("  ".join("-" * widths[k] for k in keys))
    for r in rows:
        print("  ".join(str(r.get(k, "")).rjust(widths[k]) for k in keys))


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Stone-mulch microclimate simulation for root-zone protection.",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""\
examples:
  %(prog)s daily                           Run a 24-hour thermal/pH cycle
  %(prog)s mineral --years 20              Multi-year mineral decay
  %(prog)s stress --years 20               Cumulative stress simulation
  %(prog)s shock --ambient -40 --hours 72  Thermal shock event
  %(prog)s frost --diameters 4 8 12 16     Compare frost protection by spread
  %(prog)s all --json                      Run all simulations, output JSON
""",
    )
    sub = parser.add_subparsers(dest="command", help="Simulation to run")

    # -- daily --
    p_daily = sub.add_parser("daily", help="24-hour thermal/condensation/pH cycle")
    p_daily.add_argument("--mean-temp", type=float, default=11.0, help="Daily mean temp C (default: 11)")
    p_daily.add_argument("--amplitude", type=float, default=13.0, help="Temp half-range C (default: 13)")
    p_daily.add_argument("--soil-ph", type=float, default=4.5, help="Initial soil pH (default: 4.5)")
    p_daily.add_argument("--albedo", type=float, default=0.4, help="Stone albedo (default: 0.4)")
    p_daily.add_argument("--json", action="store_true", help="Output as JSON")

    # -- mineral --
    p_min = sub.add_parser("mineral", help="Multi-year mineral decay simulation")
    p_min.add_argument("--years", type=int, default=15, help="Simulation years (default: 15)")
    p_min.add_argument("--weather-severity", type=float, default=1.0, help="Weather severity multiplier (default: 1.0)")
    p_min.add_argument("--json", action="store_true", help="Output as JSON")

    # -- stress --
    p_stress = sub.add_parser("stress", help="Cumulative stress/recovery simulation")
    p_stress.add_argument("--years", type=int, default=15, help="Simulation years (default: 15)")
    p_stress.add_argument("--insulation", type=float, default=0.85, help="Insulation factor (default: 0.85)")
    p_stress.add_argument("--json", action="store_true", help="Output as JSON")

    # -- shock --
    p_shock = sub.add_parser("shock", help="Thermal shock propagation")
    p_shock.add_argument("--root-temp", type=float, default=2.0, help="Initial root temp C (default: 2)")
    p_shock.add_argument("--ambient", type=float, default=-30.0, help="Ambient temp C (default: -30)")
    p_shock.add_argument("--hours", type=int, default=48, help="Duration hours (default: 48)")
    p_shock.add_argument("--insulation", type=float, default=0.85, help="Insulation factor (default: 0.85)")
    p_shock.add_argument("--json", action="store_true", help="Output as JSON")

    # -- frost --
    p_frost = sub.add_parser("frost", help="Lateral frost protection comparison")
    p_frost.add_argument("--diameters", type=float, nargs="+", default=[4, 8, 12, 16],
                         help="Spread diameters in feet (default: 4 8 12 16)")
    p_frost.add_argument("--external-temp", type=float, default=-45.0, help="External temp C (default: -45)")
    p_frost.add_argument("--insulation-bonus", type=float, default=0.4, help="Insulation bonus (default: 0.4)")
    p_frost.add_argument("--json", action="store_true", help="Output as JSON")

    # -- all --
    p_all = sub.add_parser("all", help="Run all simulations with defaults")
    p_all.add_argument("--json", action="store_true", help="Output as JSON")

    args = parser.parse_args()

    if args.command is None:
        parser.print_help()
        sys.exit(0)

    use_json = getattr(args, "json", False)

    if args.command == "daily":
        site = SiteParams(
            soil_ph=args.soil_ph,
            mean_temp_c=args.mean_temp,
            temp_amplitude_c=args.amplitude,
        )
        layer = StoneLayer("mulch", args.albedo, 0.005, 0.2, 0.001, 0.4)
        result = simulate_daily_cycle(site, layer)
        if use_json:
            print(json.dumps(result, indent=2))
        else:
            print("=== Daily Thermal/pH Cycle ===\n")
            _print_table(result["log"])
            print(f"\nFinal pH: {result['final_ph']:.3f}")
            print(f"Final moisture: {result['final_moisture']:.5f}")
            print(f"Total condensation: {result['total_condensation']:.5f} mm")

    elif args.command == "mineral":
        log = simulate_years(years=args.years, weather_severity=args.weather_severity)
        if use_json:
            print(json.dumps(log, indent=2))
        else:
            print("=== Multi-Year Mineral Decay ===\n")
            _print_table(log)

    elif args.command == "stress":
        log = simulate_stress_years(years=args.years, insulation_factor=args.insulation)
        if use_json:
            print(json.dumps(log, indent=2))
        else:
            print("=== Cumulative Stress / Recovery ===\n")
            _print_table(log)

    elif args.command == "shock":
        result = thermal_shock(
            root_temp=args.root_temp,
            ambient_temp=args.ambient,
            duration_hours=args.hours,
            insulation_factor=args.insulation,
        )
        if use_json:
            print(json.dumps(result, indent=2))
        else:
            print("=== Thermal Shock ===\n")
            print(f"Initial root temp: {result['initial_root_temp']} C")
            print(f"Ambient temp:      {result['ambient_temp']} C")
            print(f"Duration:          {result['duration_hours']} hours")
            print(f"Final root temp:   {result['final_root_temp']} C")
            print(f"Survived:          {'YES' if result['alive'] else 'NO'}")
            print(f"Hours survived:    {result['hours_survived']}")

    elif args.command == "frost":
        result = compare_spreads(args.diameters, args.external_temp, args.insulation_bonus)
        if use_json:
            print(json.dumps(result, indent=2))
        else:
            print("=== Lateral Frost Protection ===\n")
            _print_table(result)

    elif args.command == "all":
        site = SiteParams()
        layer = StoneLayer("mulch", 0.4, 0.005, 0.2, 0.001, 0.4)
        all_results = {
            "daily_cycle": simulate_daily_cycle(site, layer),
            "mineral_decay": simulate_years(),
            "stress": simulate_stress_years(),
            "shock": thermal_shock(site.root_temp_initial_c, -30.0, 48),
            "frost_comparison": compare_spreads([4, 8, 12, 16]),
        }
        if use_json:
            print(json.dumps(all_results, indent=2))
        else:
            print("=== Daily Cycle ===\n")
            _print_table(all_results["daily_cycle"]["log"])
            dc = all_results["daily_cycle"]
            print(f"\nFinal pH: {dc['final_ph']:.3f}  |  "
                  f"Moisture: {dc['final_moisture']:.5f}  |  "
                  f"Condensation: {dc['total_condensation']:.5f} mm\n")

            print("=== Mineral Decay ===\n")
            _print_table(all_results["mineral_decay"])
            print()

            print("=== Cumulative Stress ===\n")
            _print_table(all_results["stress"])
            print()

            shock = all_results["shock"]
            print("=== Thermal Shock ===\n")
            print(f"Root {shock['initial_root_temp']}C -> {shock['final_root_temp']}C "
                  f"at ambient {shock['ambient_temp']}C over {shock['hours_survived']}h  "
                  f"Survived: {'YES' if shock['alive'] else 'NO'}\n")

            print("=== Frost Protection ===\n")
            _print_table(all_results["frost_comparison"])


if __name__ == "__main__":
    main()
