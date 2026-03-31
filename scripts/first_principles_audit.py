# first_principles_audit.py

# Six Sigma First-Principles Validation Engine

# Run on any Python module to extract assumptions, test sensitivity,

# identify failure modes, and generate accountability reports.

# 

# DMAIC Framework:

# Define   → What does each parameter represent physically?

# Measure  → What are the defaults, ranges, units?

# Analyze  → Sensitivity analysis, Pareto of influence

# Improve  → Boundary conditions, failure modes (FMEA)

# Control  → Capability indices, control limits, verification tests

# 

# Output: JSON (machine-readable), Markdown (human-readable), CSV (spreadsheet)

# 

# Usage:

# from first_principles_audit import audit_function, audit_module, generate_report

# report = audit_function(my_function, params, ranges)

# generate_report(report, format="markdown", filepath="audit.md")

import inspect
import json
import csv
import math
import os
from dataclasses import dataclass, field, asdict
from typing import (
Dict, List, Any, Optional, Callable, Tuple, Union,
)
from collections import OrderedDict
from io import StringIO

# =========================================================================

# DEFINE -- Parameter Documentation

# =========================================================================

@dataclass
class ParameterSpec:
"""
Complete specification of a single parameter.
Forces explicit documentation of physical meaning,
source, units, and valid range.
"""
name: str
default_value: float
units: str = ""
physical_meaning: str = ""
source: str = ""               # "measured", "derived", "assumed", "literature"
valid_min: Optional[float] = None
valid_max: Optional[float] = None
uncertainty: Optional[float] = None   # ± value or % if source is "measured"
notes: str = ""

```
def is_documented(self) -> bool:
    return bool(self.physical_meaning and self.source and self.units)

def is_within_range(self, value: float) -> bool:
    if self.valid_min is not None and value < self.valid_min:
        return False
    if self.valid_max is not None and value > self.valid_max:
        return False
    return True
```

@dataclass
class AssumptionRecord:
"""An explicit assumption made by the model."""
name: str
description: str
basis: str                     # "physics", "empirical", "convention", "simplification"
falsifiable: bool = True
falsification_test: str = ""   # how to check if this assumption is wrong
impact_if_wrong: str = ""      # what breaks

# =========================================================================

# MEASURE -- Extract and Catalog

# =========================================================================

def extract_function_signature(func: Callable) -> Dict[str, Any]:
"""
Extract parameter names, defaults, and docstring from a function.
"""
sig = inspect.signature(func)
doc = inspect.getdoc(func) or ""
source_lines = ""
try:
source_lines = inspect.getsource(func)
except (OSError, TypeError):
pass

```
params = OrderedDict()
for name, p in sig.parameters.items():
    default = p.default if p.default is not inspect.Parameter.empty else None
    params[name] = {
        "name": name,
        "default": default,
        "has_default": p.default is not inspect.Parameter.empty,
        "annotation": str(p.annotation) if p.annotation is not inspect.Parameter.empty else None,
    }

return {
    "function_name": func.__name__,
    "module": func.__module__ if hasattr(func, "__module__") else "",
    "docstring": doc,
    "parameters": params,
    "source": source_lines,
}
```

def catalog_parameters(
func: Callable,
specs: Optional[Dict[str, ParameterSpec]] = None,
) -> Dict[str, Any]:
"""
Catalog all parameters with documentation status.
specs: user-provided ParameterSpec for each parameter.
"""
sig_info = extract_function_signature(func)
catalog = []

```
for name, info in sig_info["parameters"].items():
    spec = specs.get(name) if specs else None
    entry = {
        "name": name,
        "default": info["default"],
        "has_default": info["has_default"],
        "documented": spec.is_documented() if spec else False,
        "units": spec.units if spec else "UNDOCUMENTED",
        "physical_meaning": spec.physical_meaning if spec else "UNDOCUMENTED",
        "source": spec.source if spec else "UNDOCUMENTED",
        "valid_range": (
            [spec.valid_min, spec.valid_max] if spec else [None, None]
        ),
        "uncertainty": spec.uncertainty if spec else None,
    }
    catalog.append(entry)

undocumented = [e for e in catalog if not e["documented"]]

return {
    "function": sig_info["function_name"],
    "total_parameters": len(catalog),
    "documented": len(catalog) - len(undocumented),
    "undocumented": len(undocumented),
    "undocumented_names": [e["name"] for e in undocumented],
    "documentation_ratio": (
        (len(catalog) - len(undocumented)) / len(catalog)
        if catalog else 0
    ),
    "parameters": catalog,
}
```

# =========================================================================

# ANALYZE -- Sensitivity Analysis

# =========================================================================

def sensitivity_analysis(
func: Callable,
base_params: Dict[str, float],
param_ranges: Dict[str, Tuple[float, float]],
output_key: Optional[str] = None,
n_steps: int = 10,
) -> Dict[str, Any]:
"""
One-at-a-time sensitivity analysis.
Vary each parameter across its range while holding others at baseline.

```
Parameters
----------
func : callable
    Function to test. Must accept **kwargs and return a number or dict.
base_params : dict
    Baseline parameter values.
param_ranges : dict
    parameter_name → (min, max) range to sweep.
output_key : str, optional
    If func returns a dict, which key to track.
n_steps : int
    Number of steps across each range.

Returns
-------
dict with per-parameter sensitivity results and Pareto ranking.
"""
def _get_output(result):
    if isinstance(result, dict):
        if output_key and output_key in result:
            return float(result[output_key])
        # try first numeric value
        for v in result.values():
            if isinstance(v, (int, float)):
                return float(v)
        return 0.0
    return float(result)

# Baseline output
baseline_output = _get_output(func(**base_params))

results = {}
for param_name, (lo, hi) in param_ranges.items():
    if param_name not in base_params:
        continue

    sweep_values = []
    sweep_outputs = []

    for i in range(n_steps + 1):
        val = lo + (hi - lo) * i / n_steps
        test_params = dict(base_params)
        test_params[param_name] = val

        try:
            out = _get_output(func(**test_params))
        except Exception as e:
            out = None

        sweep_values.append(round(val, 6))
        sweep_outputs.append(round(out, 6) if out is not None else None)

    # Compute sensitivity metrics
    valid_outputs = [o for o in sweep_outputs if o is not None]
    if len(valid_outputs) > 1:
        output_range = max(valid_outputs) - min(valid_outputs)
        output_mean = sum(valid_outputs) / len(valid_outputs)
        output_std = math.sqrt(
            sum((o - output_mean) ** 2 for o in valid_outputs) / len(valid_outputs)
        )
        # Sensitivity coefficient: normalized output change per normalized input change
        input_range = hi - lo
        input_mean = (hi + lo) / 2
        if input_mean != 0 and output_mean != 0:
            sensitivity_coeff = (output_range / output_mean) / (input_range / input_mean)
        else:
            sensitivity_coeff = output_range
    else:
        output_range = 0
        output_mean = baseline_output
        output_std = 0
        sensitivity_coeff = 0

    results[param_name] = {
        "sweep_values": sweep_values,
        "sweep_outputs": sweep_outputs,
        "output_range": round(output_range, 6),
        "output_mean": round(output_mean, 6),
        "output_std": round(output_std, 6),
        "sensitivity_coefficient": round(sensitivity_coeff, 6),
        "baseline_value": base_params[param_name],
        "test_range": [lo, hi],
    }

# Pareto ranking (highest sensitivity first)
pareto = sorted(
    results.items(),
    key=lambda x: -abs(x[1]["sensitivity_coefficient"]),
)
pareto_ranking = [
    {"rank": i + 1, "parameter": name, "sensitivity": data["sensitivity_coefficient"]}
    for i, (name, data) in enumerate(pareto)
]

return {
    "baseline_output": baseline_output,
    "baseline_params": base_params,
    "sensitivities": results,
    "pareto_ranking": pareto_ranking,
    "dominant_parameter": pareto_ranking[0]["parameter"] if pareto_ranking else None,
}
```

# =========================================================================

# IMPROVE -- Boundary Conditions and FMEA

# =========================================================================

def boundary_test(
func: Callable,
base_params: Dict[str, float],
param_ranges: Dict[str, Tuple[float, float]],
output_key: Optional[str] = None,
) -> List[Dict[str, Any]]:
"""
Test function at boundary values (min, max, zero, negative, extreme).
Identifies where the model breaks.
"""
def _safe_call(params):
try:
result = func(**params)
if isinstance(result, dict) and output_key:
return result.get(output_key, result)
return result
except Exception as e:
return {"error": str(e)}

```
tests = []

for param_name, (lo, hi) in param_ranges.items():
    boundary_values = [
        ("minimum", lo),
        ("maximum", hi),
        ("zero", 0),
        ("negative", -abs(hi)),
        ("extreme_high", hi * 10),
        ("extreme_low", lo * 0.01 if lo > 0 else lo * 10),
    ]

    for label, val in boundary_values:
        test_params = dict(base_params)
        test_params[param_name] = val
        result = _safe_call(test_params)

        is_error = isinstance(result, dict) and "error" in result
        is_nan = False
        is_inf = False

        if isinstance(result, (int, float)):
            is_nan = math.isnan(result)
            is_inf = math.isinf(result)

        tests.append({
            "parameter": param_name,
            "boundary": label,
            "test_value": val,
            "result": str(result)[:200] if is_error else result,
            "error": is_error,
            "nan": is_nan,
            "inf": is_inf,
            "passed": not (is_error or is_nan or is_inf),
        })

return tests
```

def generate_fmea(
parameters: List[ParameterSpec],
assumptions: List[AssumptionRecord],
) -> List[Dict[str, Any]]:
"""
Failure Mode and Effects Analysis.
For each parameter and assumption, document:
- What could go wrong
- How severe it would be
- How likely it is
- How detectable it is
- Risk Priority Number (RPN)
"""
fmea = []

```
for param in parameters:
    severity = 5  # default moderate
    if param.valid_min is not None or param.valid_max is not None:
        severity = 3  # range-bounded = less severe
    if not param.is_documented():
        severity = 8  # undocumented = high severity

    occurrence = 3 if param.source == "measured" else 5 if param.source == "assumed" else 4
    detection = 2 if param.uncertainty is not None else 7

    rpn = severity * occurrence * detection

    fmea.append({
        "item": param.name,
        "type": "parameter",
        "failure_mode": f"Value outside valid range or based on wrong assumption",
        "effect": f"Model output unreliable for {param.name}",
        "severity": severity,
        "occurrence": occurrence,
        "detection": detection,
        "rpn": rpn,
        "documented": param.is_documented(),
        "source": param.source,
        "recommendation": (
            "Document physical meaning, source, and uncertainty"
            if not param.is_documented()
            else "Verify against independent measurement"
        ),
    })

for assumption in assumptions:
    severity = 7 if assumption.impact_if_wrong else 5
    occurrence = 4
    detection = 3 if assumption.falsifiable else 8

    rpn = severity * occurrence * detection

    fmea.append({
        "item": assumption.name,
        "type": "assumption",
        "failure_mode": f"Assumption invalid: {assumption.description[:80]}",
        "effect": assumption.impact_if_wrong or "Unknown",
        "severity": severity,
        "occurrence": occurrence,
        "detection": detection,
        "rpn": rpn,
        "falsifiable": assumption.falsifiable,
        "basis": assumption.basis,
        "recommendation": (
            assumption.falsification_test
            if assumption.falsification_test
            else "Define falsification test"
        ),
    })

# Sort by RPN descending (highest risk first)
fmea.sort(key=lambda x: -x["rpn"])
return fmea
```

# =========================================================================

# CONTROL -- Capability Indices and Control Limits

# =========================================================================

def capability_analysis(
outputs: List[float],
lower_spec: Optional[float] = None,
upper_spec: Optional[float] = None,
target: Optional[float] = None,
) -> Dict[str, Any]:
"""
Compute process capability indices (Cp, Cpk, Pp, Ppk).

```
Parameters
----------
outputs : list of float
    Sample of output values from simulation runs.
lower_spec : float, optional
    Lower specification limit.
upper_spec : float, optional
    Upper specification limit.
target : float, optional
    Target value.
"""
n = len(outputs)
if n < 2:
    return {"error": "Need at least 2 data points"}

mean = sum(outputs) / n
std = math.sqrt(sum((x - mean) ** 2 for x in outputs) / (n - 1))

result = {
    "n": n,
    "mean": round(mean, 6),
    "std": round(std, 6),
    "min": round(min(outputs), 6),
    "max": round(max(outputs), 6),
    "range": round(max(outputs) - min(outputs), 6),
}

if std > 0:
    if lower_spec is not None and upper_spec is not None:
        cp = (upper_spec - lower_spec) / (6 * std)
        cpu = (upper_spec - mean) / (3 * std)
        cpl = (mean - lower_spec) / (3 * std)
        cpk = min(cpu, cpl)
        result["Cp"] = round(cp, 4)
        result["Cpk"] = round(cpk, 4)
        result["Cpu"] = round(cpu, 4)
        result["Cpl"] = round(cpl, 4)

    if target is not None:
        result["bias"] = round(mean - target, 6)

    # Control limits (3-sigma)
    result["UCL"] = round(mean + 3 * std, 6)
    result["LCL"] = round(mean - 3 * std, 6)

    # Sigma level
    if upper_spec is not None:
        z_upper = (upper_spec - mean) / std
        result["z_upper"] = round(z_upper, 4)
    if lower_spec is not None:
        z_lower = (mean - lower_spec) / std
        result["z_lower"] = round(z_lower, 4)
else:
    result["note"] = "Zero variance -- all outputs identical"

return result
```

def monte_carlo_capability(
func: Callable,
param_distributions: Dict[str, Tuple[float, float]],
n_samples: int = 1000,
output_key: Optional[str] = None,
lower_spec: Optional[float] = None,
upper_spec: Optional[float] = None,
seed: Optional[int] = 42,
) -> Dict[str, Any]:
"""
Monte Carlo simulation for capability analysis.
Sample parameters from uniform distributions, run function,
collect outputs, compute capability indices.

```
Parameters
----------
param_distributions : dict
    parameter_name → (min, max) uniform distribution bounds.
"""
import random as rng
if seed is not None:
    rng.seed(seed)

outputs = []
failures = 0

for _ in range(n_samples):
    params = {
        name: rng.uniform(lo, hi)
        for name, (lo, hi) in param_distributions.items()
    }
    try:
        result = func(**params)
        if isinstance(result, dict):
            if output_key and output_key in result:
                val = float(result[output_key])
            else:
                vals = [v for v in result.values() if isinstance(v, (int, float))]
                val = vals[0] if vals else None
        else:
            val = float(result)

        if val is not None and not (math.isnan(val) or math.isinf(val)):
            outputs.append(val)
        else:
            failures += 1
    except Exception:
        failures += 1

cap = capability_analysis(outputs, lower_spec, upper_spec)
cap["n_samples"] = n_samples
cap["failures"] = failures
cap["failure_rate"] = round(failures / n_samples, 4) if n_samples > 0 else 0

return cap
```

# =========================================================================

# FULL AUDIT

# =========================================================================

def audit_function(
func: Callable,
base_params: Dict[str, float],
param_ranges: Dict[str, Tuple[float, float]],
specs: Optional[Dict[str, ParameterSpec]] = None,
assumptions: Optional[List[AssumptionRecord]] = None,
output_key: Optional[str] = None,
lower_spec: Optional[float] = None,
upper_spec: Optional[float] = None,
n_sensitivity_steps: int = 10,
n_monte_carlo: int = 1000,
) -> Dict[str, Any]:
"""
Complete Six Sigma audit of a function.

```
Returns
-------
dict with sections: define, measure, analyze, improve, control
"""
# DEFINE
sig_info = extract_function_signature(func)

# MEASURE
param_catalog = catalog_parameters(func, specs)

# ANALYZE
sens = sensitivity_analysis(
    func, base_params, param_ranges,
    output_key=output_key, n_steps=n_sensitivity_steps,
)

# IMPROVE
boundaries = boundary_test(func, base_params, param_ranges, output_key)
fmea = generate_fmea(
    list(specs.values()) if specs else [],
    assumptions or [],
)

# CONTROL
mc = monte_carlo_capability(
    func, param_ranges,
    n_samples=n_monte_carlo,
    output_key=output_key,
    lower_spec=lower_spec,
    upper_spec=upper_spec,
)

boundary_failures = [b for b in boundaries if not b["passed"]]

return {
    "function": sig_info["function_name"],
    "docstring": sig_info["docstring"],
    "define": {
        "parameters": param_catalog,
        "assumptions": [asdict(a) for a in (assumptions or [])],
    },
    "measure": {
        "baseline_params": base_params,
        "baseline_output": sens["baseline_output"],
        "documentation_ratio": param_catalog["documentation_ratio"],
        "undocumented": param_catalog["undocumented_names"],
    },
    "analyze": {
        "sensitivity": {
            name: {
                "sensitivity_coefficient": data["sensitivity_coefficient"],
                "output_range": data["output_range"],
                "output_std": data["output_std"],
            }
            for name, data in sens["sensitivities"].items()
        },
        "pareto_ranking": sens["pareto_ranking"],
        "dominant_parameter": sens["dominant_parameter"],
    },
    "improve": {
        "boundary_tests_total": len(boundaries),
        "boundary_failures": len(boundary_failures),
        "boundary_failure_details": boundary_failures,
        "fmea": fmea,
        "highest_rpn": fmea[0] if fmea else None,
    },
    "control": {
        "monte_carlo": mc,
    },
    "summary": {
        "documentation_ratio": param_catalog["documentation_ratio"],
        "dominant_parameter": sens["dominant_parameter"],
        "boundary_failure_rate": (
            len(boundary_failures) / len(boundaries)
            if boundaries else 0
        ),
        "monte_carlo_failure_rate": mc.get("failure_rate", 0),
        "Cpk": mc.get("Cpk"),
        "overall_grade": _grade(param_catalog, boundary_failures, mc),
    },
}
```

def _grade(catalog, boundary_failures, mc) -> str:
"""Simple overall grade based on audit results."""
score = 0

```
# Documentation
doc_ratio = catalog["documentation_ratio"]
if doc_ratio >= 0.9:
    score += 3
elif doc_ratio >= 0.5:
    score += 1

# Boundary robustness
if len(boundary_failures) == 0:
    score += 3
elif len(boundary_failures) <= 3:
    score += 1

# Monte Carlo
if mc.get("failure_rate", 1) < 0.01:
    score += 2
elif mc.get("failure_rate", 1) < 0.05:
    score += 1

cpk = mc.get("Cpk")
if cpk is not None and cpk >= 1.33:
    score += 2
elif cpk is not None and cpk >= 1.0:
    score += 1

if score >= 9:
    return "A -- Production ready"
elif score >= 6:
    return "B -- Usable with caveats"
elif score >= 3:
    return "C -- Needs improvement"
else:
    return "D -- Not validated"
```

# =========================================================================

# REPORT GENERATION

# =========================================================================

def generate_report(
audit_result: Dict[str, Any],
fmt: str = "markdown",
filepath: Optional[str] = None,
) -> str:
"""
Generate audit report in markdown, JSON, or CSV.

```
Parameters
----------
fmt : "markdown", "json", or "csv"
filepath : optional file path to write to
"""
if fmt == "json":
    content = json.dumps(audit_result, indent=2, default=str)

elif fmt == "csv":
    content = _to_csv(audit_result)

else:
    content = _to_markdown(audit_result)

if filepath:
    with open(filepath, "w", encoding="utf-8") as f:
        f.write(content)

return content
```

def _to_markdown(r: Dict) -> str:
lines = []
a = lines.append

```
a(f"# First-Principles Audit: `{r['function']}`\n")
a(f"_{r.get('docstring', '')}_\n")

# Summary
s = r["summary"]
a("## Summary\n")
a(f"| Metric | Value |")
a(f"|--------|-------|")
a(f"| Overall Grade | **{s['overall_grade']}** |")
a(f"| Documentation Ratio | {s['documentation_ratio']:.0%} |")
a(f"| Dominant Parameter | {s['dominant_parameter']} |")
a(f"| Boundary Failure Rate | {s['boundary_failure_rate']:.0%} |")
a(f"| Monte Carlo Failure Rate | {s['monte_carlo_failure_rate']:.1%} |")
if s.get("Cpk") is not None:
    a(f"| Cpk | {s['Cpk']:.3f} |")
a("")

# Define
a("## Define -- Parameters\n")
params = r["define"]["parameters"]["parameters"]
a("| Parameter | Default | Units | Source | Documented |")
a("|-----------|---------|-------|--------|------------|")
for p in params:
    doc = "Yes" if p["documented"] else "**NO**"
    a(f"| {p['name']} | {p['default']} | {p['units']} | {p['source']} | {doc} |")
a("")

if r["define"]["assumptions"]:
    a("## Define -- Assumptions\n")
    for ass in r["define"]["assumptions"]:
        a(f"- **{ass['name']}**: {ass['description']}")
        a(f"  - Basis: {ass['basis']}")
        a(f"  - Falsifiable: {ass['falsifiable']}")
        if ass.get("falsification_test"):
            a(f"  - Test: {ass['falsification_test']}")
    a("")

# Analyze
a("## Analyze -- Sensitivity Ranking\n")
a("| Rank | Parameter | Sensitivity Coefficient |")
a("|------|-----------|------------------------|")
for item in r["analyze"]["pareto_ranking"]:
    a(f"| {item['rank']} | {item['parameter']} | {item['sensitivity']:.4f} |")
a("")

# Improve
a("## Improve -- Boundary Failures\n")
bf = r["improve"]["boundary_failure_details"]
if bf:
    a("| Parameter | Boundary | Value | Error |")
    a("|-----------|----------|-------|-------|")
    for b in bf:
        a(f"| {b['parameter']} | {b['boundary']} | {b['test_value']} | {b.get('result', '')!s:.60} |")
else:
    a("No boundary failures detected.\n")
a("")

if r["improve"]["fmea"]:
    a("## Improve -- FMEA (Top 5 by RPN)\n")
    a("| Item | Type | RPN | Severity | Occurrence | Detection | Recommendation |")
    a("|------|------|-----|----------|------------|-----------|----------------|")
    for item in r["improve"]["fmea"][:5]:
        a(f"| {item['item']} | {item['type']} | {item['rpn']} | {item['severity']} | {item['occurrence']} | {item['detection']} | {item['recommendation']:.50} |")
a("")

# Control
mc = r["control"]["monte_carlo"]
a("## Control -- Monte Carlo Capability\n")
a(f"| Metric | Value |")
a(f"|--------|-------|")
a(f"| Samples | {mc.get('n', 'N/A')} |")
a(f"| Mean | {mc.get('mean', 'N/A')} |")
a(f"| Std Dev | {mc.get('std', 'N/A')} |")
a(f"| Range | {mc.get('range', 'N/A')} |")
a(f"| Failures | {mc.get('failures', 'N/A')} ({mc.get('failure_rate', 0):.1%}) |")
if mc.get("Cp") is not None:
    a(f"| Cp | {mc['Cp']:.3f} |")
if mc.get("Cpk") is not None:
    a(f"| Cpk | {mc['Cpk']:.3f} |")
if mc.get("UCL") is not None:
    a(f"| UCL (3σ) | {mc['UCL']:.4f} |")
    a(f"| LCL (3σ) | {mc['LCL']:.4f} |")
a("")

return "\n".join(lines)
```

def _to_csv(r: Dict) -> str:
"""Flatten audit to CSV rows."""
buf = StringIO()
writer = csv.writer(buf)

```
# Parameters
writer.writerow(["Section", "Item", "Metric", "Value"])

for p in r["define"]["parameters"]["parameters"]:
    writer.writerow(["parameter", p["name"], "default", p["default"]])
    writer.writerow(["parameter", p["name"], "units", p["units"]])
    writer.writerow(["parameter", p["name"], "source", p["source"]])
    writer.writerow(["parameter", p["name"], "documented", p["documented"]])

for item in r["analyze"]["pareto_ranking"]:
    writer.writerow(["sensitivity", item["parameter"], "rank", item["rank"]])
    writer.writerow(["sensitivity", item["parameter"], "coefficient", item["sensitivity"]])

for b in r["improve"]["boundary_failure_details"]:
    writer.writerow(["boundary", b["parameter"], b["boundary"], b["test_value"]])

for item in r["improve"]["fmea"]:
    writer.writerow(["fmea", item["item"], "rpn", item["rpn"]])

mc = r["control"]["monte_carlo"]
for k in ["mean", "std", "Cp", "Cpk", "failures", "failure_rate"]:
    if k in mc:
        writer.writerow(["capability", "monte_carlo", k, mc[k]])

writer.writerow(["summary", "grade", "overall", r["summary"]["overall_grade"]])

return buf.getvalue()
```

# =========================================================================

# LAYER 2 -- BIAS DETECTION AND DESIGN CHOICE ACCOUNTABILITY

# =========================================================================

# 

# Layer 1 audits the mechanics: "Does this code work correctly?"

# Layer 2 audits the choices: "Why was this code written THIS way?"

# 

# Catches human bias (domain assumptions, cultural defaults)

# and AI bias (optimization tendency, recency weighting, complexity preference).

# ------------------

# Known Bias Patterns

# ------------------

KNOWN_BIAS_PATTERNS = {
"optimization_bias": {
"description": "Tendency to frame all systems as optimization problems",
"indicators": [
"Single objective function without constraints",
"Parameters chosen to maximize one output",
"No accounting for what is sacrificed",
],
"common_in": ["AI models", "economics", "industrial engineering"],
},
"recency_bias": {
"description": "Over-weighting recent data or methods over established physics",
"indicators": [
"Default values from recent papers only",
"No comparison to long-term baselines",
"Ignoring pre-industrial or indigenous approaches",
],
"common_in": ["AI models", "policy analysis"],
},
"complexity_bias": {
"description": "Preferring complex models when simpler ones explain the data",
"indicators": [
"More parameters than the system requires",
"Nested functions without clear physical justification",
"Sensitivity analysis shows most parameters don't matter",
],
"common_in": ["AI models", "academic research"],
},
"simplification_bias": {
"description": "Dropping terms that are inconvenient to model",
"indicators": [
"Externalized costs set to zero",
"Long-term feedback loops omitted",
"Coupling terms between subsystems missing",
],
"common_in": ["industrial models", "economic models"],
},
"linearity_bias": {
"description": "Assuming linear relationships where nonlinear dynamics exist",
"indicators": [
"All rates are constant",
"No threshold or saturation effects",
"No feedback between state variables",
],
"common_in": ["AI models", "spreadsheet analysis"],
},
"survivorship_bias": {
"description": "Training on successful systems, ignoring failed ones",
"indicators": [
"Default parameters reflect 'best case'",
"No failure mode in the model",
"Validation only against working examples",
],
"common_in": ["AI models", "business analysis"],
},
"scale_bias": {
"description": "Assuming results at one scale apply at another",
"indicators": [
"No scale parameter in the model",
"Same equations for lab and field",
"No spatial or temporal resolution check",
],
"common_in": ["AI models", "engineering extrapolation"],
},
"externalization_bias": {
"description": "Omitting costs borne by parties outside the model boundary",
"indicators": [
"No pollution, waste, or degradation terms",
"Efficiency calculated without full lifecycle",
"System boundary excludes downstream effects",
],
"common_in": ["industrial models", "economic models", "AI trained on corporate data"],
},
}

# ------------------

# Design Choice Record

# ------------------

@dataclass
class DesignChoice:
"""
Documents a specific modeling decision.
Forces the modeler to state what alternatives existed
and why this one was chosen.
"""
name: str                          # e.g., "responsiveness_degradation_form"
chosen: str                        # e.g., "dR = -k1*signal + k2*(1-R)"
alternatives: List[str]            # what else could have been used
reason: str                        # why this one was picked
bias_risk: List[str]               # which bias patterns this choice is susceptible to
impact_on_output: str = ""         # how this choice shapes results
who_decided: str = ""              # "human", "AI:claude", "AI:gemini", "literature"

# ------------------

# Bias Flag Engine

# ------------------

def flag_biases(
specs: List[ParameterSpec],
assumptions: List[AssumptionRecord],
design_choices: List[DesignChoice],
sensitivity_result: Optional[Dict] = None,
) -> List[Dict[str, Any]]:
"""
Scan parameters, assumptions, and design choices for known bias patterns.

```
Returns list of bias flags with evidence and severity.
"""
flags = []

# Check parameters
undocumented_sources = [s for s in specs if s.source in ("assumed", "")]
if len(undocumented_sources) > len(specs) * 0.3:
    flags.append({
        "bias": "simplification_bias",
        "evidence": f"{len(undocumented_sources)}/{len(specs)} parameters assumed or undocumented",
        "severity": "high",
        "recommendation": "Trace each parameter to measurement or derivation",
    })

all_derived = all(s.source == "derived" for s in specs if s.source)
if all_derived and len(specs) > 3:
    flags.append({
        "bias": "complexity_bias",
        "evidence": "All parameters derived -- no direct measurements anchor the model",
        "severity": "medium",
        "recommendation": "Include at least one directly measured parameter as ground truth",
    })

# Check assumptions
unfalsifiable = [a for a in assumptions if not a.falsifiable]
if unfalsifiable:
    flags.append({
        "bias": "survivorship_bias",
        "evidence": f"{len(unfalsifiable)} unfalsifiable assumptions: {[a.name for a in unfalsifiable]}",
        "severity": "high",
        "recommendation": "Every assumption must have a falsification test",
    })

no_test = [a for a in assumptions if a.falsifiable and not a.falsification_test]
if no_test:
    flags.append({
        "bias": "simplification_bias",
        "evidence": f"{len(no_test)} assumptions lack falsification tests: {[a.name for a in no_test]}",
        "severity": "medium",
        "recommendation": "Define specific observations that would prove each assumption wrong",
    })

physics_basis = [a for a in assumptions if a.basis == "physics"]
convention_basis = [a for a in assumptions if a.basis == "convention"]
if len(convention_basis) > len(physics_basis):
    flags.append({
        "bias": "recency_bias",
        "evidence": f"More assumptions based on convention ({len(convention_basis)}) than physics ({len(physics_basis)})",
        "severity": "medium",
        "recommendation": "Derive from first principles where possible",
    })

# Check design choices
for dc in design_choices:
    if not dc.alternatives:
        flags.append({
            "bias": "optimization_bias",
            "evidence": f"Design choice '{dc.name}' lists no alternatives -- was only one option considered?",
            "severity": "high",
            "recommendation": "Document at least 2 alternative formulations",
        })

    for bias_name in dc.bias_risk:
        if bias_name in KNOWN_BIAS_PATTERNS:
            pattern = KNOWN_BIAS_PATTERNS[bias_name]
            flags.append({
                "bias": bias_name,
                "evidence": f"Design choice '{dc.name}' self-identified as susceptible: {pattern['description']}",
                "severity": "medium",
                "source": dc.who_decided,
                "recommendation": f"Test alternative formulations: {dc.alternatives[:2]}",
            })

# Check sensitivity results for complexity bias
if sensitivity_result:
    pareto = sensitivity_result.get("pareto_ranking", [])
    if len(pareto) > 3:
        low_impact = [p for p in pareto if abs(p["sensitivity"]) < 0.05]
        if len(low_impact) > len(pareto) * 0.5:
            flags.append({
                "bias": "complexity_bias",
                "evidence": f"{len(low_impact)}/{len(pareto)} parameters have sensitivity < 0.05 -- model may be over-parameterized",
                "severity": "medium",
                "recommendation": "Consider removing or fixing low-impact parameters",
            })

# Check for externalization bias
has_externalization_term = any(
    "external" in s.name.lower() or "waste" in s.name.lower()
    or "pollution" in s.name.lower() or "degradation" in s.name.lower()
    for s in specs
)
if not has_externalization_term and len(specs) > 3:
    flags.append({
        "bias": "externalization_bias",
        "evidence": "No parameter explicitly accounts for externalized costs, waste, or degradation",
        "severity": "high",
        "recommendation": "Add terms for costs borne outside the model boundary",
    })

# Check for linearity bias
linear_assumptions = [
    a for a in assumptions
    if "constant" in a.description.lower() or "linear" in a.description.lower()
]
if linear_assumptions:
    flags.append({
        "bias": "linearity_bias",
        "evidence": f"Assumptions imply linearity: {[a.name for a in linear_assumptions]}",
        "severity": "medium",
        "recommendation": "Test with nonlinear or time-varying formulations",
    })

# Sort by severity
severity_order = {"high": 0, "medium": 1, "low": 2}
flags.sort(key=lambda f: severity_order.get(f.get("severity", "low"), 3))

return flags
```

# ------------------

# Formulation Comparison

# ------------------

def compare_formulations(
formulations: Dict[str, Callable],
base_params: Dict[str, float],
param_ranges: Dict[str, Tuple[float, float]],
output_key: Optional[str] = None,
n_monte_carlo: int = 500,
lower_spec: Optional[float] = None,
upper_spec: Optional[float] = None,
seed: int = 42,
) -> Dict[str, Any]:
"""
Run the same audit on multiple alternative formulations
and compare their outputs.

```
Parameters
----------
formulations : dict
    name → callable, each implementing the same interface.

Returns
-------
dict with per-formulation results and divergence analysis.
"""
results = {}

for name, func in formulations.items():
    # Sensitivity
    sens = sensitivity_analysis(
        func, base_params, param_ranges,
        output_key=output_key, n_steps=10,
    )

    # Monte Carlo
    mc = monte_carlo_capability(
        func, param_ranges,
        n_samples=n_monte_carlo,
        output_key=output_key,
        lower_spec=lower_spec,
        upper_spec=upper_spec,
        seed=seed,
    )

    results[name] = {
        "baseline_output": sens["baseline_output"],
        "dominant_parameter": sens["dominant_parameter"],
        "pareto": sens["pareto_ranking"],
        "mc_mean": mc.get("mean"),
        "mc_std": mc.get("std"),
        "mc_range": mc.get("range"),
        "Cpk": mc.get("Cpk"),
        "failure_rate": mc.get("failure_rate"),
    }

# Divergence analysis
baselines = {n: r["baseline_output"] for n, r in results.items()}
means = {n: r["mc_mean"] for n, r in results.items() if r["mc_mean"] is not None}

if len(means) > 1:
    mean_vals = list(means.values())
    spread = max(mean_vals) - min(mean_vals)
    avg = sum(mean_vals) / len(mean_vals)
    divergence_ratio = spread / abs(avg) if avg != 0 else float("inf")
else:
    divergence_ratio = 0

# Which parameters rank differently across formulations?
dominant_params = {n: r["dominant_parameter"] for n, r in results.items()}
dominant_agreement = len(set(dominant_params.values())) == 1

return {
    "formulations": results,
    "divergence": {
        "baseline_outputs": baselines,
        "mc_means": means,
        "divergence_ratio": round(divergence_ratio, 4),
        "dominant_parameters": dominant_params,
        "dominant_agreement": dominant_agreement,
    },
    "recommendation": (
        "Formulations agree -- choice has low impact"
        if divergence_ratio < 0.1 and dominant_agreement
        else "Formulations diverge -- design choice significantly affects results"
    ),
}
```

# ------------------

# Extended Audit (Layer 1 + Layer 2)

# ------------------

def full_audit(
func: Callable,
base_params: Dict[str, float],
param_ranges: Dict[str, Tuple[float, float]],
specs: Optional[Dict[str, ParameterSpec]] = None,
assumptions: Optional[List[AssumptionRecord]] = None,
design_choices: Optional[List[DesignChoice]] = None,
alternative_formulations: Optional[Dict[str, Callable]] = None,
output_key: Optional[str] = None,
lower_spec: Optional[float] = None,
upper_spec: Optional[float] = None,
n_sensitivity_steps: int = 10,
n_monte_carlo: int = 1000,
) -> Dict[str, Any]:
"""
Complete audit: Layer 1 (mechanics) + Layer 2 (bias/design choices).
"""
# Layer 1
layer1 = audit_function(
func, base_params, param_ranges,
specs=specs, assumptions=assumptions,
output_key=output_key,
lower_spec=lower_spec, upper_spec=upper_spec,
n_sensitivity_steps=n_sensitivity_steps,
n_monte_carlo=n_monte_carlo,
)

```
# Layer 2: Bias flags
bias_flags = flag_biases(
    list(specs.values()) if specs else [],
    assumptions or [],
    design_choices or [],
    sensitivity_result={"pareto_ranking": layer1["analyze"]["pareto_ranking"]},
)

# Layer 2: Formulation comparison
formulation_comparison = None
if alternative_formulations:
    all_formulations = {"primary": func}
    all_formulations.update(alternative_formulations)
    formulation_comparison = compare_formulations(
        all_formulations, base_params, param_ranges,
        output_key=output_key,
        n_monte_carlo=n_monte_carlo,
        lower_spec=lower_spec, upper_spec=upper_spec,
    )

# Layer 2: Design choice documentation
design_doc = []
if design_choices:
    for dc in design_choices:
        design_doc.append({
            "name": dc.name,
            "chosen": dc.chosen,
            "alternatives": dc.alternatives,
            "reason": dc.reason,
            "bias_risk": dc.bias_risk,
            "who_decided": dc.who_decided,
            "alternatives_tested": (
                formulation_comparison is not None
                and any(
                    alt in (alternative_formulations or {})
                    for alt in dc.alternatives
                )
            ),
        })

# Combine
layer1["bias_detection"] = {
    "flags": bias_flags,
    "high_severity_count": len([f for f in bias_flags if f.get("severity") == "high"]),
    "design_choices": design_doc,
    "formulation_comparison": formulation_comparison,
}

# Update grade to account for bias
high_bias = len([f for f in bias_flags if f.get("severity") == "high"])
if high_bias >= 3:
    layer1["summary"]["bias_grade"] = "FAIL -- Multiple high-severity biases detected"
elif high_bias >= 1:
    layer1["summary"]["bias_grade"] = "WARNING -- High-severity bias detected"
elif bias_flags:
    layer1["summary"]["bias_grade"] = "CAUTION -- Medium-severity biases present"
else:
    layer1["summary"]["bias_grade"] = "PASS -- No significant biases detected"

return layer1
```
